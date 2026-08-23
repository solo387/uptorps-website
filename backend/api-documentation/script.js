/**
 * API Documentation JavaScript
 * Handles navigation, code formatting, and interactive features
 */

document.addEventListener("DOMContentLoaded", function () {
  initializeNavigation();
  initializeCodeBlocks();
  initializeScrollSpy();
  initializeCollapsibleSections();
  initializeCopyButton();
});

/**
 * Initialize navigation - Set active links based on current page
 */
function initializeNavigation() {
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll(".sidebar-nav a, .app-links a");

  navLinks.forEach((link) => {
    const href = link.getAttribute("href");

    // Check if link matches current path
    if (
      currentPath.includes(href) ||
      (currentPath.includes("accounts") && href.includes("accounts"))
    ) {
      link.classList.add("active");
    } else {
      link.classList.remove("active");
    }
  });
}

/**
 * Initialize syntax highlighting for code blocks
 */
function initializeCodeBlocks() {
  const codeBlocks = document.querySelectorAll(".code-block");

  codeBlocks.forEach((block) => {
    // Add line numbers if needed
    const lines = block.textContent.split("\n");
    if (lines.length > 1) {
      block.style.position = "relative";
    }
  });
}

/**
 * Initialize scroll spy for sidebar
 */
function initializeScrollSpy() {
  const sections = document.querySelectorAll(".endpoint-card");
  const navLinks = document.querySelectorAll(".sidebar-nav a");

  window.addEventListener("scroll", () => {
    let current = "";

    sections.forEach((section) => {
      const sectionTop = section.offsetTop;
      const sectionHeight = section.clientHeight;

      if (window.scrollY >= sectionTop - 200) {
        current = section.getAttribute("id");
      }
    });

    navLinks.forEach((link) => {
      link.classList.remove("active");

      if (current) {
        const activeLink = document.querySelector(
          `.sidebar-nav a[href="#${current}"]`,
        );
        if (activeLink) {
          activeLink.classList.add("active");
        }
      }
    });
  });
}

/**
 * Initialize collapsible sections for better mobile experience
 */
function initializeCollapsibleSections() {
  const sectionTitles = document.querySelectorAll(".section-title");

  sectionTitles.forEach((title) => {
    title.style.cursor = "pointer";
    title.addEventListener("click", function () {
      const section = this.closest(".section");
      const content = section.querySelector(
        "table, .code-block, .request-example, p",
      );

      if (content) {
        content.style.display =
          content.style.display === "none" ? "block" : "none";
        this.style.opacity = content.style.display === "none" ? "0.6" : "1";
      }
    });
  });
}

/**
 * Add copy button to code blocks
 */
function initializeCopyButton() {
  const codeBlocks = document.querySelectorAll(".code-block");

  codeBlocks.forEach((block, index) => {
    // Create wrapper
    const wrapper = document.createElement("div");
    wrapper.style.position = "relative";
    wrapper.style.marginTop = "12px";

    block.parentNode.insertBefore(wrapper, block);
    wrapper.appendChild(block);

    // Create copy button
    const copyBtn = document.createElement("button");
    copyBtn.textContent = "📋 Copy";
    copyBtn.className = "copy-btn";
    copyBtn.style.cssText = `
            position: absolute;
            top: 8px;
            right: 8px;
            padding: 6px 12px;
            background-color: rgba(255, 255, 255, 0.1);
            color: #e2e8f0;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.3s ease;
            z-index: 10;
        `;

    copyBtn.addEventListener("mouseenter", function () {
      this.style.backgroundColor = "rgba(255, 255, 255, 0.2)";
      this.style.borderColor = "rgba(255, 255, 255, 0.4)";
    });

    copyBtn.addEventListener("mouseleave", function () {
      this.style.backgroundColor = "rgba(255, 255, 255, 0.1)";
      this.style.borderColor = "rgba(255, 255, 255, 0.2)";
    });

    copyBtn.addEventListener("click", function (e) {
      e.preventDefault();
      const text = block.textContent;

      navigator.clipboard
        .writeText(text)
        .then(() => {
          const originalText = copyBtn.textContent;
          copyBtn.textContent = "✓ Copied!";

          setTimeout(() => {
            copyBtn.textContent = originalText;
          }, 2000);
        })
        .catch((err) => {
          console.error("Copy failed:", err);
        });
    });

    wrapper.appendChild(copyBtn);
  });
}

/**
 * Utility function to format JSON for display
 */
function formatJSON(obj) {
  return JSON.stringify(obj, null, 2);
}

/**
 * Utility function to create parameter table rows
 */
function createParamRow(name, type, required, description) {
  return `
        <tr>
            <td><span class="param-name">${name}</span> <span class="param-type">${type}</span></td>
            <td>${description}</td>
            <td>${required ? '<span class="required-badge">REQUIRED</span>' : '<span class="optional-badge">OPTIONAL</span>'}</td>
        </tr>
    `;
}

/**
 * Smooth scroll to section
 */
function smoothScroll(target) {
  const element = document.querySelector(target);
  if (element) {
    element.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

/**
 * Handle sidebar link clicks
 */
document.addEventListener("click", function (e) {
  if (e.target.matches(".sidebar-nav a")) {
    e.preventDefault();
    const href = e.target.getAttribute("href");

    // If it's an internal anchor
    if (href.startsWith("#")) {
      smoothScroll(href);
    } else {
      window.location.href = href;
    }
  }
});

/**
 * Initialize tabs if present
 */
function initializeTabs() {
  const tabs = document.querySelectorAll(".tabs");

  tabs.forEach((tabGroup) => {
    const tabButtons = tabGroup.querySelectorAll(".tab-btn");
    const tabContents = tabGroup.querySelectorAll(".tab-content");

    tabButtons.forEach((btn, index) => {
      btn.addEventListener("click", () => {
        // Remove active from all
        tabButtons.forEach((b) => b.classList.remove("active"));
        tabContents.forEach((c) => (c.style.display = "none"));

        // Add active to clicked
        btn.classList.add("active");
        tabContents[index].style.display = "block";
      });
    });
  });
}

/**
 * Export utilities for external use
 */
window.APIDocUtils = {
  formatJSON,
  createParamRow,
  smoothScroll,
  initializeNavigation,
  initializeCodeBlocks,
};
