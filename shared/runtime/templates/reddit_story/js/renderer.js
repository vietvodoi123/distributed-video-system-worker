
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

if (!fs.existsSync(renderedPath)) {
  throw new Error(`Rendered HTML not found: ${renderedPath}`);
}

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
        if (!input.trim()) {
          throw new Error("No input received from stdin.");
        }

        const segments = JSON.parse(input);

        if (!Array.isArray(segments)) {
          throw new Error("Input must be an array of segments.");
        }

        resolve(segments);
      } catch (err) {
        reject(err);
      }
    });

    process.stdin.on("error", reject);
  });
}

// ========================================
// DIRS
// ========================================

fs.mkdirSync(frameDir, {
  recursive: true,
});

// ========================================
// CONFIG
// ========================================

const NUM_WORKERS = 1;

const CHROME_PATH =
  "C:/Program Files/Google/Chrome/Application/chrome.exe";

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
// HTML ESCAPE
// ========================================

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ========================================
// VALIDATE SEGMENTS
// ========================================

function validateSegments(segments) {
  if (!Array.isArray(segments)) {
    throw new Error("Segments must be an array.");
  }

  if (!segments.length) {
    throw new Error("No segments provided.");
  }

  for (let i = 0; i < segments.length; i++) {
    const segment = segments[i];

    if (!segment || typeof segment !== "object") {
      throw new Error(
        `Invalid segment at input index ${i}. Expected object.`,
      );
    }

    if (
      segment.line_index !== undefined &&
      segment.line_index !== null &&
      !Number.isInteger(Number(segment.line_index))
    ) {
      throw new Error(
        `Invalid line_index at input index ${i}: ${segment.line_index}`,
      );
    }

    if (segment.line_text === undefined || segment.line_text === null) {
      throw new Error(
        `Missing line_text at input index ${i}.`,
      );
    }
  }
}

// ========================================
// CREATE INDEXED SEGMENTS
// ========================================

function createIndexedSegments(segments) {
  return segments.map((segment, index) => ({
    ...segment,

    // Renderer index is ALWAYS based on the actual
    // position in the rendered DOM.
    render_index: index,
  }));
}

// ========================================
// BUILD HTML
// ========================================

function buildHtml(indexedSegments) {
  const linesHtml = indexedSegments
    .map((segment) => {
      const renderIndex = segment.render_index;
      const lineText = escapeHtml(segment.line_text);

      return `
        <span
          class="segment"
          data-index="${renderIndex}"
        >${lineText}</span>
      `;
    })
    .join("\n");

  if (!template.includes("{{LINES}}")) {
    throw new Error(
      'Template does not contain "{{LINES}}" placeholder.',
    );
  }

  return template.replace("{{LINES}}", linesHtml);
}

// ========================================
// CREATE BROWSER
// ========================================

async function createBrowser() {
  return puppeteer.launch({
    executablePath: CHROME_PATH,

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
}

// ========================================
// WORKER
// ========================================

async function renderWorker(tasks, indexedSegments) {
  let browser = null;

  try {
    // ======================================
    // BROWSER
    // ======================================

    browser = await createBrowser();

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

    // ======================================
    // BUILD HTML ONCE
    // ======================================

    const html = buildHtml(indexedSegments);

    // ======================================
    // LOAD PAGE
    // ======================================

    await page.setContent(html, {
      waitUntil: "domcontentloaded",
    });

    // ======================================
    // WAIT FOR FONTS
    // ======================================

    await page.evaluate(async () => {
      if (document.fonts) {
        await document.fonts.ready;
      }
    });

    // ======================================
    // WAIT FOR SEGMENTS
    // ======================================

    await page.waitForSelector(".segment", {
      timeout: 30000,
    });

    // ======================================
    // VERIFY DOM
    // ======================================

    const domInfo = await page.evaluate(() => {
      const elements = Array.from(
        document.querySelectorAll(".segment"),
      );

      return {
        count: elements.length,

        indexes: elements.map((el) =>
          el.getAttribute("data-index"),
        ),

        textLengths: elements.map(
          (el) => el.textContent?.length ?? 0,
        ),
      };
    });

    console.log(
      `[Renderer] Input segments: ${indexedSegments.length}`,
    );

    console.log(
      `[Renderer] DOM segments: ${domInfo.count}`,
    );

    // ======================================
    // DOM COUNT CHECK
    // ======================================

    if (domInfo.count !== indexedSegments.length) {
      const expectedIndexes = indexedSegments.map(
        (segment) => String(segment.render_index),
      );

      const actualIndexes = domInfo.indexes;

      const missingIndexes = expectedIndexes.filter(
        (index) => !actualIndexes.includes(index),
      );

      const extraIndexes = actualIndexes.filter(
        (index) => !expectedIndexes.includes(index),
      );

      throw new Error(
        [
          "Segment count mismatch.",
          `Input: ${indexedSegments.length}`,
          `DOM: ${domInfo.count}`,
          `Missing indexes: ${
            missingIndexes.length
              ? missingIndexes.join(", ")
              : "none"
          }`,
          `Extra indexes: ${
            extraIndexes.length
              ? extraIndexes.join(", ")
              : "none"
          }`,
        ].join(" "),
      );
    }

    // ======================================
    // VERIFY DOM INDEXES
    // ======================================

    const invalidDomIndexes = domInfo.indexes.filter(
      (value, index) => value !== String(index),
    );

    if (invalidDomIndexes.length) {
      console.error(
        "[Renderer] Invalid DOM indexes:",
        invalidDomIndexes,
      );

      throw new Error(
        "DOM segment indexes are not sequential.",
      );
    }

    // ======================================
    // CACHE DOM
    // ======================================

    await page.evaluate(() => {
      window.segmentElements = Array.from(
        document.querySelectorAll(".segment"),
      );

      window.currentHighlight = null;
    });

    // ======================================
    // VERIFY CACHE
    // ======================================

    const cachedCount = await page.evaluate(() => {
      return window.segmentElements?.length ?? 0;
    });

    if (cachedCount !== indexedSegments.length) {
      throw new Error(
        `Cached segment count mismatch: expected=${indexedSegments.length}, actual=${cachedCount}`,
      );
    }

    // ======================================
    // RENDER TASKS
    // ======================================

    for (const segment of tasks) {
      try {
        // ==================================
        // RESOLVE RENDER INDEX
        // ==================================

        const lineIndex = Number(segment.render_index);

        if (!Number.isInteger(lineIndex)) {
          throw new Error(
            `Invalid render_index: ${segment.render_index}`,
          );
        }

        // ==================================
        // RANGE CHECK
        // ==================================

        if (
          lineIndex < 0 ||
          lineIndex >= indexedSegments.length
        ) {
          throw new Error(
            [
              `Render index ${lineIndex} is out of range.`,
              `Total segments: ${indexedSegments.length}`,
              `Original line_index: ${segment.line_index}`,
            ].join(" "),
          );
        }

        // ==================================
        // DEBUG
        // ==================================

        console.log(
          `[Renderer] Rendering segment ` +
            `${lineIndex}/${indexedSegments.length - 1}` +
            ` | line_index=${segment.line_index}`,
        );

        // ==================================
        // SCROLL ACTIVE SEGMENT
        // ==================================

        await page.evaluate((index) => {
          const elements = window.segmentElements;

          if (!Array.isArray(elements)) {
            throw new Error(
              "segmentElements not initialized.",
            );
          }

          const el = elements[index];

          if (!el) {
            throw new Error(
              `Segment ${index} not found. ` +
                `DOM contains ${elements.length} segments.`,
            );
          }

          // Remove previous highlight.

          if (window.currentHighlight) {
            window.currentHighlight.classList.remove(
              "highlight",
            );
          }

          // Add current highlight.

          el.classList.add("highlight");

          window.currentHighlight = el;

          // Scroll.

          el.scrollIntoView({
            behavior: "instant",
            block: "center",
          });
        }, lineIndex);

        // ==================================
        // FRAME PATH
        // ==================================

        const framePath = path.join(
          frameDir,
          `frame${String(lineIndex).padStart(4, "0")}.jpg`,
        );

        // ==================================
        // WAIT FOR PAINT
        // ==================================

        await page.evaluate(
          () =>
            new Promise((resolve) =>
              requestAnimationFrame(() => resolve()),
            ),
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

        // ==================================
        // PROGRESS
        // ==================================

        completed++;

        bar.update(completed);
      } catch (err) {
        console.error(
          `[Renderer] Failed to render segment`,
        );

        console.error(
          JSON.stringify(
            {
              line_index: segment.line_index,
              render_index: segment.render_index,
              line_text:
                String(segment.line_text ?? "").slice(
                  0,
                  200,
                ),
              error: err?.message,
            },
            null,
            2,
          ),
        );

        throw err;
      }
    }
  } finally {
    // ======================================
    // CLOSE BROWSER
    // ======================================

    if (browser) {
      try {
        await browser.close();
      } catch (err) {
        console.error(
          "[Renderer] Failed to close browser:",
          err,
        );
      }
    }
  }
}

// ========================================
// MAIN
// ========================================

(async () => {
  try {
    // ======================================
    // READ INPUT
    // ======================================

    const segments = await readSegments();

    // ======================================
    // VALIDATE INPUT
    // ======================================

    validateSegments(segments);

    // ======================================
    // INDEX SEGMENTS
    // ======================================

    const indexedSegments =
      createIndexedSegments(segments);

    console.log(
      `[Renderer] Received ${indexedSegments.length} segments.`,
    );

    // ======================================
    // SHOW LAST SEGMENT
    // ======================================

    const lastSegment =
      indexedSegments[indexedSegments.length - 1];

    console.log(
      `[Renderer] Last segment:`,
      JSON.stringify(
        {
          render_index: lastSegment.render_index,
          line_index: lastSegment.line_index,
        },
        null,
        2,
      ),
    );

    // ======================================
    // CREATE WORKER CHUNKS
    // ======================================

    const chunked = Array.from(
      {
        length: NUM_WORKERS,
      },
      () => [],
    );

    indexedSegments.forEach((segment, i) => {
      chunked[i % NUM_WORKERS].push(segment);
    });

    // ======================================
    // START PROGRESS
    // ======================================

    bar.start(indexedSegments.length, 0);

    // ======================================
    // RUN WORKERS
    // ======================================

    await Promise.all(
      chunked.map((tasks) =>
        renderWorker(
          tasks,
          indexedSegments,
        ),
      ),
    );

    // ======================================
    // STOP PROGRESS
    // ======================================

    bar.stop();

    console.log(
      "🎉 Frames rendered.",
    );
  } catch (err) {
    try {
      bar.stop();
    } catch (_) {}

    console.error(
      "[FATAL]",
      err,
    );

    if (err && err.stack) {
      console.error(err.stack);
    }

    process.exit(1);
  }
})();

