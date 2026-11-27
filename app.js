const DIRECTIONS = {
  up: { dx: 0, dy: -1, arrow: "↑", label: "góra" },
  right: { dx: 1, dy: 0, arrow: "→", label: "prawo" },
  down: { dx: 0, dy: 1, arrow: "↓", label: "dół" },
  left: { dx: -1, dy: 0, arrow: "←", label: "lewo" },
};

const MODES = {
  standard: { title: "PRZYGODA", width: 5, height: 4, limit: 12, delay: 520 },
  turbo: { title: "TURBO", width: 11, height: 9, limit: 24, delay: 300 },
  ultra: { title: "ULTRA", width: 21, height: 17, limit: 48, delay: 180 },
};

const SCRATCH_PROJECTS = {
  "01_Urodzinowa_misja.sb3": "Urodzinowa misja",
  "02_Zepsuty_balon.sb3": "Zepsuty balon",
  "03_Studio_przyjecia.sb3": "Studio przyjęcia",
  "04_Slonce_start.sb3": "Misja Słońce · start",
  "05_Slonce_gotowe.sb3": "Misja Słońce · przykład",
};

const ui = {
  robotTab: document.querySelector("#robotTab"),
  scratchTab: document.querySelector("#scratchTab"),
  robotView: document.querySelector("#robotView"),
  scratchView: document.querySelector("#scratchView"),
  modeTitle: document.querySelector("#modeTitle"),
  score: document.querySelector("#scoreValue"),
  level: document.querySelector("#levelText"),
  boardText: document.querySelector("#boardText"),
  board: document.querySelector("#board"),
  status: document.querySelector("#status"),
  program: document.querySelector("#program"),
  limit: document.querySelector("#limitText"),
  start: document.querySelector("#startButton"),
  undo: document.querySelector("#undoButton"),
  clear: document.querySelector("#clearButton"),
  hint: document.querySelector("#hintButton"),
  next: document.querySelector("#nextButton"),
  projectName: document.querySelector("#selectedProjectName"),
  playerSlot: document.querySelector("#playerSlot"),
  loadProject: document.querySelector("#loadProject"),
  openPlayer: document.querySelector("#openPlayer"),
  experimentProject: document.querySelector("#experimentProject"),
  installHelp: document.querySelector("#installHelp"),
  installDialog: document.querySelector("#installDialog"),
};

const state = {
  mode: "standard",
  level: 1,
  wins: 0,
  round: 1,
  solved: false,
  busy: false,
  commands: [],
  position: null,
  trail: [],
  puzzle: null,
  rng: makeRng(Date.now() >>> 0),
  selectedProject: "01_Urodzinowa_misja.sb3",
};

function makeRng(seed) {
  let value = seed || 1;
  return () => {
    value |= 0;
    value = value + 0x6d2b79f5 | 0;
    let result = Math.imul(value ^ value >>> 15, 1 | value);
    result = result + Math.imul(result ^ result >>> 7, 61 | result) ^ result;
    return ((result ^ result >>> 14) >>> 0) / 4294967296;
  };
}

function randomInt(rng, maximum) {
  return Math.floor(rng() * maximum);
}

function shuffle(items, rng) {
  for (let index = items.length - 1; index > 0; index -= 1) {
    const other = randomInt(rng, index + 1);
    [items[index], items[other]] = [items[other], items[index]];
  }
  return items;
}

function sample(items, count, rng) {
  return shuffle([...items], rng).slice(0, count);
}

function pointKey(point) {
  return `${point[0]},${point[1]}`;
}

function fromKey(key) {
  return key.split(",").map(Number);
}

function boardContains(board, point) {
  return point[0] >= 0 && point[0] < board.width && point[1] >= 0 && point[1] < board.height;
}

function advance(board, position, direction) {
  const vector = DIRECTIONS[direction];
  const destination = [position[0] + vector.dx, position[1] + vector.dy];
  if (!boardContains(board, destination)) return { error: "Brzeg planszy" };
  if (board.obstacles.has(pointKey(destination))) return { error: board.mode === "ultra" ? "Ściana labiryntu" : "Kamień na drodze" };
  return { position: destination };
}

function shortestPaths(board, start) {
  const paths = new Map([[pointKey(start), []]]);
  const queue = [start];
  for (let cursor = 0; cursor < queue.length; cursor += 1) {
    const position = queue[cursor];
    const route = paths.get(pointKey(position));
    for (const [direction, vector] of Object.entries(DIRECTIONS)) {
      const step = advance(board, position, direction);
      if (step.error) continue;
      const key = pointKey(step.position);
      if (paths.has(key)) continue;
      paths.set(key, [...route, direction]);
      queue.push(step.position);
    }
  }
  return paths;
}

function countTurns(route) {
  let turns = 0;
  for (let index = 1; index < route.length; index += 1) {
    if (route[index] !== route[index - 1]) turns += 1;
  }
  return turns;
}

function makeStandardPuzzle(level, rng, excluded = new Set()) {
  const targetSteps = level + 2;
  const minimumTurns = Math.min(3, Math.floor((level + 1) / 2));
  const points = Array.from({ length: 20 }, (_, index) => [index % 5, Math.floor(index / 5)]);
  for (let attempt = 0; attempt < 500; attempt += 1) {
    const obstacles = new Set(sample(points, level - 1, rng).map(pointKey));
    const available = points.filter(point => !obstacles.has(pointKey(point)));
    const start = available[randomInt(rng, available.length)];
    const board = { ...MODES.standard, mode: "standard", start, treasure: start, obstacles };
    const paths = shortestPaths(board, start);
    const candidates = [...paths.entries()].filter(([key, route]) =>
      !excluded.has(key) && route.length === targetSteps && countTurns(route) >= minimumTurns
    );
    if (!candidates.length) continue;
    const [treasureKey, solution] = candidates[randomInt(rng, candidates.length)];
    board.treasure = fromKey(treasureKey);
    return { board, solution };
  }
  throw new Error("Nie udało się wylosować planszy trybu Przygoda.");
}

function makeTurboPuzzle(level, rng, excluded = new Set()) {
  const width = MODES.turbo.width;
  const height = MODES.turbo.height;
  const targetSteps = 8 + 2 * (level - 1);
  const points = Array.from({ length: width * height }, (_, index) => [index % width, Math.floor(index / width)]);
  for (let attempt = 0; attempt < 500; attempt += 1) {
    const obstacles = new Set(sample(points, 8 + 2 * level, rng).map(pointKey));
    const available = points.filter(point => !obstacles.has(pointKey(point)));
    const start = available[randomInt(rng, available.length)];
    const board = { ...MODES.turbo, mode: "turbo", start, treasure: start, obstacles };
    const paths = shortestPaths(board, start);
    if (paths.size !== available.length) continue;
    const routeCounts = new Map([[pointKey(start), 1]]);
    for (const [key, route] of paths) {
      if (!route.length) continue;
      const point = fromKey(key);
      let total = 0;
      for (const [direction, vector] of Object.entries(DIRECTIONS)) {
        const previous = [point[0] - vector.dx, point[1] - vector.dy];
        const previousKey = pointKey(previous);
        if (paths.get(previousKey)?.length === route.length - 1) {
          total = Math.min(2, total + (routeCounts.get(previousKey) || 0));
        }
      }
      routeCounts.set(key, total);
    }
    const candidates = [...paths.entries()].filter(([key, route]) =>
      !excluded.has(key) && route.length === targetSteps && routeCounts.get(key) >= 2 && countTurns(route) >= 2
    );
    if (!candidates.length) continue;
    const [treasureKey, solution] = candidates[randomInt(rng, candidates.length)];
    board.treasure = fromKey(treasureKey);
    return { board, solution };
  }
  throw new Error("Nie udało się wylosować otwartej planszy Turbo.");
}

function addMazeFrontier(cell, cells, openCells, frontier) {
  const [x, y] = cell;
  for (const neighbor of [[x + 2, y], [x - 2, y], [x, y + 2], [x, y - 2]]) {
    const key = pointKey(neighbor);
    if (cells.has(key) && !openCells.has(key)) frontier.push([cell, neighbor]);
  }
}

function makeUltraPuzzle(level, rng, excluded = new Set()) {
  const width = MODES.ultra.width;
  const height = MODES.ultra.height;
  const targetSteps = 20 + 5 * (level - 1);
  const cells = new Set();
  const cellPoints = [];
  for (let y = 1; y < height - 1; y += 2) {
    for (let x = 1; x < width - 1; x += 2) {
      const point = [x, y];
      cells.add(pointKey(point));
      cellPoints.push(point);
    }
  }
  for (let attempt = 0; attempt < 250; attempt += 1) {
    const root = cellPoints[randomInt(rng, cellPoints.length)];
    const openCells = new Set([pointKey(root)]);
    const openCorridors = new Set();
    const frontier = [];
    addMazeFrontier(root, cells, openCells, frontier);
    while (frontier.length) {
      const index = randomInt(rng, frontier.length);
      const [[x, y], [nextX, nextY]] = frontier.splice(index, 1)[0];
      const next = [nextX, nextY];
      if (openCells.has(pointKey(next))) continue;
      openCells.add(pointKey(next));
      openCorridors.add(pointKey([(x + nextX) / 2, (y + nextY) / 2]));
      addMazeFrontier(next, cells, openCells, frontier);
    }
    const openSpaces = new Set([...openCells, ...openCorridors]);
    const obstacles = new Set();
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        if (!openSpaces.has(pointKey([x, y]))) obstacles.add(pointKey([x, y]));
      }
    }
    const junctions = new Set();
    for (const point of cellPoints) {
      const [x, y] = point;
      const degree = [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]
        .filter(neighbor => openSpaces.has(pointKey(neighbor))).length;
      if (degree >= 3) junctions.add(pointKey(point));
    }
    const starts = shuffle([...cellPoints], rng);
    for (const start of starts) {
      const board = { ...MODES.ultra, mode: "ultra", start, treasure: start, obstacles };
      const paths = shortestPaths(board, start);
      const candidates = [...paths.entries()].filter(([key, route]) => {
        if (excluded.has(key) || route.length !== targetSteps) return false;
        let point = [...start];
        let choices = 0;
        for (const direction of route.slice(0, -1)) {
          const vector = DIRECTIONS[direction];
          point = [point[0] + vector.dx, point[1] + vector.dy];
          if (junctions.has(pointKey(point))) choices += 1;
        }
        return choices >= 3;
      });
      if (!candidates.length) continue;
      const [treasureKey, solution] = candidates[randomInt(rng, candidates.length)];
      board.treasure = fromKey(treasureKey);
      return { board, solution };
    }
  }
  throw new Error("Nie udało się wylosować labiryntu Ultra.");
}

function generatePuzzle(mode, level, rng, excluded) {
  if (mode === "turbo") return makeTurboPuzzle(level, rng, excluded);
  if (mode === "ultra") return makeUltraPuzzle(level, rng, excluded);
  return makeStandardPuzzle(level, rng, excluded);
}

function startCampaign(mode = "standard") {
  state.mode = mode;
  state.level = 1;
  state.wins = 0;
  state.round = 1;
  state.solved = false;
  state.rng = makeRng((Date.now() ^ Math.floor(Math.random() * 0xffffffff)) >>> 0);
  state.puzzle = generatePuzzle(mode, state.level, state.rng, new Set());
  state.position = [...state.puzzle.board.start];
  state.trail = [pointKey(state.position)];
  state.commands = [];
  state.busy = false;
  state.statusMessage = "Ułóż strzałki i naciśnij START.";
  state.statusType = "";
  render();
}

function cellAriaLabel(x, y, tile) {
  if (tile.robot) return `Robot, kolumna ${x + 1}, wiersz ${y + 1}`;
  if (tile.treasure) return `Skarb, kolumna ${x + 1}, wiersz ${y + 1}`;
  if (tile.obstacle) return `Przeszkoda, kolumna ${x + 1}, wiersz ${y + 1}`;
  return `Pole, kolumna ${x + 1}, wiersz ${y + 1}`;
}

function renderBoard() {
  const { board } = state.puzzle;
  ui.board.replaceChildren();
  ui.board.style.gridTemplateColumns = `repeat(${board.width}, minmax(0, 1fr))`;
  ui.board.setAttribute("aria-rowcount", board.height);
  ui.board.setAttribute("aria-colcount", board.width);
  for (let y = 0; y < board.height; y += 1) {
    for (let x = 0; x < board.width; x += 1) {
      const key = pointKey([x, y]);
      const robot = state.position[0] === x && state.position[1] === y;
      const treasure = board.treasure[0] === x && board.treasure[1] === y;
      const obstacle = board.obstacles.has(key);
      const tile = document.createElement("div");
      tile.className = "cell";
      tile.setAttribute("role", "gridcell");
      tile.setAttribute("aria-label", cellAriaLabel(x, y, { robot, treasure, obstacle }));
      tile.dataset.x = x;
      tile.dataset.y = y;
      if (state.trail.includes(key)) tile.classList.add("visited");
      if (obstacle) tile.classList.add("obstacle");
      if (treasure) tile.classList.add("treasure");
      if (robot) tile.classList.add("robot");
      if (x === board.start[0] && y === board.start[1]) tile.classList.add("start");
      tile.textContent = robot ? "R" : treasure ? "★" : obstacle ? "" : key === pointKey(board.start) ? "S" : "";
      ui.board.append(tile);
    }
  }
}

function setStatus(message, type = "") {
  state.statusMessage = message;
  state.statusType = type;
  ui.status.textContent = message;
  ui.status.className = `status ${type ? `is-${type}` : ""}`;
}

function renderProgram() {
  ui.program.replaceChildren();
  if (!state.commands.length) {
    const empty = document.createElement("span");
    empty.className = "program-empty";
    empty.textContent = "Dodaj pierwszy ruch";
    ui.program.append(empty);
    return;
  }
  state.commands.forEach((move, index) => {
    const chip = document.createElement("span");
    chip.className = "move-chip";
    if (state.activeIndex === index) chip.classList.add("active");
    chip.textContent = DIRECTIONS[move].arrow;
    chip.setAttribute("aria-label", `Ruch ${index + 1}: ${DIRECTIONS[move].label}`);
    ui.program.append(chip);
  });
}

function render() {
  const config = MODES[state.mode];
  ui.modeTitle.textContent = config.title;
  ui.score.textContent = `${state.wins} ${state.wins === 1 ? "skarb" : "skarbów"}`;
  ui.level.textContent = `Poziom ${state.level} / 6 · Runda ${state.round}`;
  ui.boardText.textContent = `Plansza ${config.width} × ${config.height}`;
  ui.limit.textContent = config.limit;
  document.querySelectorAll("[data-mode]").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.mode === state.mode));
  });
  renderBoard();
  renderProgram();
  ui.status.textContent = state.statusMessage;
  ui.status.className = `status ${state.statusType ? `is-${state.statusType}` : ""}`;
  ui.next.disabled = !state.solved || state.busy;
  ui.start.disabled = state.busy || state.commands.length === 0;
  document.querySelectorAll("[data-move]").forEach(button => { button.disabled = state.busy || state.solved; });
  ui.undo.disabled = state.busy || state.solved || state.commands.length === 0;
  ui.clear.disabled = state.busy || state.solved || state.commands.length === 0;
  ui.hint.disabled = state.busy || state.solved;
}

function addMove(direction) {
  if (state.busy || state.solved) return;
  const maxCommands = MODES[state.mode].limit;
  if (state.commands.length >= maxCommands) {
    setStatus(`Limit programu: ${maxCommands} ruchów.`, "error");
    return;
  }
  state.commands.push(direction);
  state.position = [...state.puzzle.board.start];
  state.trail = [pointKey(state.position)];
  state.activeIndex = null;
  setStatus("Program ułożony. Sprawdź trasę robota.");
  render();
}

function resetRobot() {
  state.position = [...state.puzzle.board.start];
  state.trail = [pointKey(state.position)];
  state.activeIndex = null;
}

function wait(milliseconds) {
  return new Promise(resolve => window.setTimeout(resolve, milliseconds));
}

async function runProgram() {
  if (state.busy || state.solved) return;
  if (!state.commands.length) {
    setStatus("Najpierw dodaj ruchy.", "error");
    return;
  }
  state.busy = true;
  resetRobot();
  render();
  const config = MODES[state.mode];
  for (let index = 0; index < state.commands.length; index += 1) {
    state.activeIndex = index;
    render();
    await wait(config.delay);
    const step = advance(state.puzzle.board, state.position, state.commands[index]);
    if (step.error) {
      state.busy = false;
      state.activeIndex = null;
      setStatus(`Ruch ${index + 1}: ${step.error}. Zmień strzałkę i spróbuj ponownie.`, "error");
      render();
      return;
    }
    state.position = step.position;
    state.trail.push(pointKey(state.position));
  }
  state.busy = false;
  state.activeIndex = null;
  if (state.position[0] === state.puzzle.board.treasure[0] && state.position[1] === state.puzzle.board.treasure[1]) {
    state.solved = true;
    state.wins += 1;
    setStatus("Skarb zdobyty! Wybierz kolejną rundę, gdy będziecie gotowi.", "success");
  } else {
    setStatus("Robot zakończył program. Skarb jeszcze czeka — popraw trasę.", "error");
  }
  render();
}

function nextRound() {
  if (!state.solved || state.busy) return;
  state.level = Math.min(6, state.wins + 1);
  state.round += 1;
  const previous = pointKey(state.puzzle.board.treasure);
  state.puzzle = generatePuzzle(state.mode, state.level, state.rng, new Set([previous]));
  state.solved = false;
  state.commands = [];
  resetRobot();
  setStatus("Nowa plansza. Ułóż strzałki i zaplanuj drogę.");
  render();
}

function showHint() {
  const firstMoves = state.puzzle.solution.slice(0, 2).map(move => DIRECTIONS[move].arrow).join(" ");
  setStatus(`Jedna z poprawnych tras zaczyna się tak: ${firstMoves}`);
}

function changeView(view) {
  const showRobot = view === "robot";
  ui.robotView.hidden = !showRobot;
  ui.scratchView.hidden = showRobot;
  ui.robotTab.classList.toggle("is-active", showRobot);
  ui.scratchTab.classList.toggle("is-active", !showRobot);
  ui.robotTab.setAttribute("aria-selected", String(showRobot));
  ui.scratchTab.setAttribute("aria-selected", String(!showRobot));
}

function setScratchProject(filename) {
  state.selectedProject = filename;
  ui.projectName.textContent = SCRATCH_PROJECTS[filename];
  document.querySelectorAll("[data-project]").forEach(button => {
    const selected = button.dataset.project === filename;
    button.classList.toggle("is-selected", selected);
    button.setAttribute("aria-pressed", String(selected));
  });
  const projectUrl = new URL(`./Scratch_Urodzinowa_Misja/projekty/${encodeURIComponent(filename)}`, window.location.href).href;
  const playerUrl = `https://turbowarp.org/embed?project_url=${encodeURIComponent(projectUrl)}&autoplay`;
  const editorUrl = new URL("https://turbowarp.org/editor");
  editorUrl.searchParams.set("project_url", projectUrl);
  editorUrl.searchParams.set("project_title", SCRATCH_PROJECTS[filename]);
  ui.openPlayer.href = playerUrl;
  ui.experimentProject.href = editorUrl.href;
  ui.playerSlot.innerHTML = "";
  const loadButton = document.createElement("button");
  loadButton.className = "load-project";
  loadButton.type = "button";
  loadButton.innerHTML = '<span class="play-icon" aria-hidden="true">▶</span><span>Uruchom projekt</span><small>Wczyta się bezpłatny player Scratch w przeglądarce</small>';
  loadButton.addEventListener("click", () => {
    const frame = document.createElement("iframe");
    frame.title = `Projekt Scratch: ${SCRATCH_PROJECTS[filename]}`;
    frame.allow = "fullscreen; autoplay; clipboard-read; clipboard-write";
    frame.allowFullscreen = true;
    frame.loading = "lazy";
    frame.src = playerUrl;
    ui.playerSlot.replaceChildren(frame);
  }, { once: true });
  ui.playerSlot.append(loadButton);
}

document.querySelectorAll("[data-mode]").forEach(button => {
  button.addEventListener("click", () => startCampaign(button.dataset.mode));
});
document.querySelectorAll("[data-move]").forEach(button => {
  button.addEventListener("click", () => addMove(button.dataset.move));
});
document.querySelectorAll("[data-project]").forEach(button => {
  button.addEventListener("click", () => setScratchProject(button.dataset.project));
});
ui.robotTab.addEventListener("click", () => changeView("robot"));
ui.scratchTab.addEventListener("click", () => changeView("scratch"));
ui.start.addEventListener("click", runProgram);
ui.undo.addEventListener("click", () => {
  if (state.busy || state.solved) return;
  state.commands.pop();
  resetRobot();
  setStatus("Ostatni ruch cofnięty.");
  render();
});
ui.clear.addEventListener("click", () => {
  if (state.busy || state.solved) return;
  state.commands = [];
  resetRobot();
  setStatus("Program wyczyszczony.");
  render();
});
ui.hint.addEventListener("click", showHint);
ui.next.addEventListener("click", nextRound);
ui.installHelp.addEventListener("click", () => ui.installDialog.showModal());

document.addEventListener("keydown", event => {
  if (event.target instanceof HTMLInputElement || event.target instanceof HTMLButtonElement) return;
  const keyMoves = { ArrowUp: "up", ArrowRight: "right", ArrowDown: "down", ArrowLeft: "left" };
  if (keyMoves[event.key]) {
    event.preventDefault();
    addMove(keyMoves[event.key]);
  } else if (event.key.toLowerCase() === "s") {
    runProgram();
  } else if (event.key.toLowerCase() === "u") {
    ui.undo.click();
  } else if (event.key.toLowerCase() === "r") {
    ui.clear.click();
  }
});

if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
  window.addEventListener("load", () => navigator.serviceWorker.register("./sw.js").catch(() => {}));
}

startCampaign();
setScratchProject(state.selectedProject);