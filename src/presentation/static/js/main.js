"use strict";

class Carousel {
  constructor(root, intervalMs = 5000) {
    this.slides = root.querySelectorAll(".banner__slide");
    this.dots = root.querySelectorAll(".banner__dots button");
    this.index = 0;
    this.dots.forEach((dot, i) => dot.addEventListener("click", () => this.show(i)));
    this.show(0);
    setInterval(() => this.show((this.index + 1) % this.slides.length), intervalMs);
  }

  show(i) {
    this.index = i;
    this.slides.forEach((s, k) => s.classList.toggle("is-active", k === i));
    this.dots.forEach((d, k) => d.classList.toggle("is-active", k === i));
  }
}

class CategoryMenu {
  constructor(toggle, menu) {
    this.toggle = toggle;
    this.menu = menu;
    if (window.matchMedia("(max-width: 900px)").matches) this.setOpen(false);
    toggle.addEventListener("click", () => this.setOpen(this.menu.hidden));
  }

  setOpen(open) {
    this.menu.hidden = !open;
    this.toggle.setAttribute("aria-expanded", String(open));
  }
}

class SearchLoader {
  constructor(form, template, target) {
    form.addEventListener("submit", () => {
      target.replaceChildren(template.content.cloneNode(true));
    });
  }
}

class ConfirmAction {
  constructor(form) {
    this.form = form;
    this.message = form.dataset.confirm;
    form.addEventListener("submit", (event) => {
      if (!window.confirm(this.message)) event.preventDefault();
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const carousel = document.querySelector("[data-carousel]");
  if (carousel) new Carousel(carousel);

  const toggle = document.querySelector("[data-menu-toggle]");
  const menu = document.querySelector("[data-menu]");
  if (toggle && menu) new CategoryMenu(toggle, menu);

  const form = document.querySelector("[data-loading-form]");
  const template = document.getElementById("loading-template");
  const content = document.querySelector(".content");
  if (form && template && content) new SearchLoader(form, template, content);

  document.querySelectorAll("form[data-confirm]").forEach(
    (form) => new ConfirmAction(form));
});
