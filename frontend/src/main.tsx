import { createRoot } from "react-dom/client";
import { createTheme, MantineProvider, Pill } from "@mantine/core";
import "@mantine/core/styles.css";
import "./style.css";
import "./features/workspace/foundation.css";
import App from "./App";
import { prepareHelp } from "./features/help/support";

const theme = createTheme({
  fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif',
  headings: {
    fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif',
    fontWeight: "650",
  },
  primaryColor: "signal",
  primaryShade: 7,
  defaultRadius: "md",
  components: {
    Pill: Pill.extend({ defaultProps: { removeButtonProps: { "aria-label": "Remove selected item" } } }),
  },
  radius: { xs: "4px", sm: "6px", md: "8px", lg: "12px", xl: "16px" },
  colors: {
    signal: ["#f5f3fc", "#eae6f7", "#d0cbea", "#b7aedb", "#9a8dcd",
      "#7b6cc1", "#6259b8", "#5148a4", "#423a8b", "#332c6c"],
    graphite: ["#f4f5f7", "#e4e7eb", "#cbd1d9", "#a7b0bc", "#7e8897",
      "#5b6472", "#434b57", "#2f353f", "#1f242c", "#11151b"],
    // A few existing controls still refer to Mantine's old color name.
    forest: ["#f4f5f7", "#e4e7eb", "#cbd1d9", "#a7b0bc", "#7e8897",
      "#5b6472", "#434b57", "#2f353f", "#1f242c", "#11151b"],
  },
});

void prepareHelp().then(() => createRoot(document.getElementById("root")!).render(
  <MantineProvider theme={theme} forceColorScheme="light">
    <App />
  </MantineProvider>,
));
