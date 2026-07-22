const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer");
const cliProgress = require("cli-progress");

// ========================================
// INPUTS
// ========================================

const frameDir = process.argv[2];

const renderedPath = process.argv[3];

if (!frameDir) {
  throw new Error("Missing frames directory");
}

if (!renderedPath) {
  throw new Error("Missing rendered.html path");
}
// ========================================
// LOAD TEMPLATE
// ========================================

const template = fs.readFileSync(renderedPath, "utf-8");

// ========================================
// LOAD SEGMENTS FROM STDIN
// ========================================

async function readSegments() {
  return new Promise((resolve, reject) => {
    let input = "";

    process.stdin.setEncoding("utf8");

    process.stdin.on("data", (chunk) => {
      input += chunk;
    });

    process.stdin.on("end", () => {
      try {
        const segments = JSON.parse(input);

        if (!Array.isArray(segments)) {
          throw new Error("Input must be an array of segments.");
        }

        resolve(segments);
      } catch (err) {
        reject(err);
      }
    });
  });
}

// ========================================
// DIRS
// ========================================

fs.mkdirSync(frameDir, { recursive: true });

// ========================================
// CONFIG
// ========================================

const NUM_WORKERS = 1;

// ========================================
// PROGRESS
// ========================================

const bar = new cliProgress.SingleBar({
  format: "📷 Render | {bar} | {value}/{total} | ETA: {eta_formatted}",

  barCompleteChar: "\u2588",

  barIncompleteChar: "\u2591",

  hideCursor: true,
});

let completed = 0;

// ========================================
// WORKER
// ========================================

async function renderWorker(tasks, indexedSegments) {
  const browser = await puppeteer.launch({
    executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
    headless: "new",
    args: [
      "--no-sandbox",
      "--disable-setuid-sandbox",

      "--disable-dev-shm-usage",

      "--disable-background-networking",

      "--disable-renderer-backgrounding",

      "--mute-audio",
    ],
  });

  const page = await browser.newPage();

  await page.setViewport({
    width: 1280,

    height: 720,
  });

  await page.emulateMediaFeatures([
    {
      name: "prefers-reduced-motion",
      value: "reduce",
    },
  ]);

  // ==================================
  // BUILD HTML ONCE
  // ==================================

  const html = template.replace(
    "{{LINES}}",

    indexedSegments
      .map(
        (s) => `

              <span
                class="segment"
                data-index="${s.render_index}"
              >
                ${s.line_text}
              </span>

            `,
      )
      .join("\n"),
  );

  // ==================================
  // LOAD PAGE
  // ==================================

  await page.setContent(
    html,

    {
      waitUntil: "domcontentloaded",
    },
  );

  await page.evaluate(() => document.fonts.ready);

  await page.waitForSelector(".segment");
  // ==================================
  // CACHE DOM
  // ==================================

  await page.evaluate(() => {
    window.segmentElements = Array.from(document.querySelectorAll(".segment"));

    window.currentHighlight = null;
  });

  for (const segment of tasks) {
    try {
      const line_index = segment.line_index;

      // ==================================
      // SCROLL ACTIVE SEGMENT
      // ==================================

      await page.evaluate(
        (index) => {
          const elements = window.segmentElements;

          if (!elements) {
            throw new Error("segmentElements not initialized.");
          }

          if (window.currentHighlight) {
            window.currentHighlight.classList.remove("highlight");
          }

          const el = elements[index];

          if (!el) {
            throw new Error(`Segment ${index} not found.`);
          }

          el.classList.add("highlight");

          window.currentHighlight = el;

          el.scrollIntoView({
            behavior: "instant",

            block: "center",
          });
        },

        line_index,
      );

      // ==================================
      // FRAME PATH
      // ==================================

      const framePath = path.join(
        frameDir,

        `frame${String(line_index).padStart(4, "0")}.jpg`,
      );

      await page.evaluate(
        () => new Promise((resolve) => requestAnimationFrame(resolve)),
      );
      // ==================================
      // SCREENSHOT
      // ==================================

      await page.screenshot({
        path: framePath,

        type: "jpeg",

        quality: 85,

        optimizeForSpeed: true,

        captureBeyondViewport: false,

        fromSurface: true,
      });

      completed++;

      bar.update(completed);
    } catch (err) {
      console.error("[Renderer] ERROR:", err);

      throw err;
    }
  }

  await browser.close();
}

// ========================================
// MAIN
// ========================================

(async () => {
  try {
    const segments = await readSegments();

    if (!segments.length) {
      throw new Error("No segments provided.");
    }

    const indexedSegments = segments.map((segment, index) => ({
      ...segment,

      render_index: index,
    }));

    const chunked = Array.from({ length: NUM_WORKERS }, () => []);

    indexedSegments.forEach((segment, i) => {
      chunked[i % NUM_WORKERS].push(segment);
    });

    bar.start(indexedSegments.length, 0);

    await Promise.all(
      chunked.map((tasks) => renderWorker(tasks, indexedSegments)),
    );

    bar.stop();

    console.log("🎉 Frames rendered.");
  } catch (err) {
    console.error("[FATAL]", err);

    if (err && err.stack) {
      console.error(err.stack);
    }

    process.exit(1);
  }
})();
