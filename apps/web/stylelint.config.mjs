import shared from "../../stylelint.config.mjs";

export default {
  ...shared,
  rules: {
    ...shared.rules,
    "no-descending-specificity": null,
  },
};
