import "@webwoven/design-tokens";
import "./styles/index.css";

import { mount } from "svelte";
import App from "./App.svelte";

const target = document.getElementById("app");

if (!target) {
  throw new Error("Webwoven could not find its application mount point.");
}

mount(App, { target });
