/**
 * captcha-solver.js
 * 
 * Automatise la résolution du CAPTCHA de façon invisible.
 * 
 * COMMENT L'UTILISER :
 * Ajoute cette ligne dans index.html, après script.js :
 *   <script src="/frontend/captcha-solver.js"></script>
 * 
 * COMMENT ÇA FONCTIONNE :
 * 1. Intercepte la réponse de /api/captcha/challenge
 * 2. Envoie les images + classe cible à /api/captcha/solve
 * 3. Le backend détecte avec YOLO/RT-DETR et retourne les bons indices
 * 4. Les cases se cochent automatiquement avec des délais naturels
 * 5. VERIFY se clique tout seul
 */

(function () {

  // ─── Utilitaires ─────────────────────────────────────────────────────────────

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  function randomDelay(min = 180, max = 520) {
    return Math.floor(Math.random() * (max - min) + min);
  }

  // ─── Interception de /api/captcha/challenge ───────────────────────────────────

  const originalFetch = window.fetch;

  window.fetch = async function (...args) {
    const response = await originalFetch(...args);
    const url = typeof args[0] === "string" ? args[0] : args[0]?.url || "";

    if (url.includes("/api/captcha/challenge")) {
      const cloned = response.clone();

      cloned.json().then(async (data) => {
        if (data && data.images && data.target_class) {

          await sleep(randomDelay(400, 800));

          try {
            const solveResponse = await originalFetch("http://localhost:8000/api/captcha/solve", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                images: data.images,
                target_class: data.target_class
              })
            });

            const solveData = await solveResponse.json();

            if (solveData.success && Array.isArray(solveData.correct_indices)) {
              await solveAutomatically(solveData.correct_indices);
            }

          } catch (err) {
            console.warn("[solver] Erreur:", err);
          }
        }
      }).catch(() => {});
    }

    return response;
  };

  // ─── Cocher les bonnes cases automatiquement ─────────────────────────────────

  async function solveAutomatically(correctIndices) {
    const grid = document.getElementById("captchaGrid");
    if (!grid) return;

    await waitForCells(grid, 9);

    const cells = grid.querySelectorAll(".captcha-cell");
    if (!cells || cells.length === 0) return;

    for (const index of correctIndices) {
      if (cells[index]) {
        await sleep(randomDelay(200, 600));
        cells[index].click();
      }
    }

    await sleep(randomDelay(600, 1000));

    const verifyBtn = document.getElementById("verifyBtn");
    if (verifyBtn) {
      verifyBtn.click();
    }
  }

  // ─── Attendre que les cases soient dans le DOM ────────────────────────────────

  function waitForCells(grid, minCount, timeout = 6000) {
    return new Promise((resolve) => {
      const start = Date.now();

      const check = () => {
        const cells = grid.querySelectorAll(".captcha-cell");
        if (cells.length >= minCount) { resolve(cells); return; }
        if (Date.now() - start > timeout) { resolve(cells); return; }
        requestAnimationFrame(check);
      };

      check();
    });
  }

})();