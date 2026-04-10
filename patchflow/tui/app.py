from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, Header, ListItem, ListView, Static

from patchflow.analysis.scope import ScopeAnalysisResult, analyze_branch_scope
from patchflow.cleaning.branch_builder import CleanBranchError, create_clean_branch
from patchflow.tui.presenter import branch_summary_text, cluster_label, detail_text


class PatchflowApp(App[None]):
    CSS = """
    Screen {
      layout: vertical;
    }

    #main {
      height: 1fr;
    }

    #left-pane, #right-pane {
      width: 1fr;
      height: 1fr;
      border: solid $panel;
      padding: 1;
    }

    #summary, #details, #status-line {
      height: auto;
    }

    #cluster-list {
      height: 1fr;
      border: round $accent;
      margin-top: 1;
    }

    #actions {
      height: auto;
      padding: 1;
      dock: bottom;
    }

    Button {
      margin-right: 1;
    }
    """

    BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh"), ("c", "clean", "Clean")]

    def __init__(self, branch_name: str | None = None) -> None:
        super().__init__()
        self.branch_name = branch_name
        self.result: ScopeAnalysisResult | None = None
        self.selected_cluster_index: int | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            with Vertical(id="left-pane"):
                yield Static("Loading...", id="summary")
                yield ListView(id="cluster-list")
            with Vertical(id="right-pane"):
                yield Static("No cluster selected.", id="details")
                yield Static("", id="status-line")
        with Horizontal(id="actions"):
            yield Button("Refresh", id="refresh")
            yield Button("Clean", id="clean")
            yield Button("Quit", id="quit")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_analysis()

    def refresh_analysis(self, cluster_index: int | None = None) -> None:
        self.result = analyze_branch_scope(cluster_index=cluster_index)
        self.selected_cluster_index = self.result.selected_cluster_index
        self._render()

    def _render(self) -> None:
        assert self.result is not None
        self.query_one("#summary", Static).update(branch_summary_text(self.result))
        self.query_one("#details", Static).update(detail_text(self.result, self.branch_name))
        list_view = self.query_one("#cluster-list", ListView)
        list_view.clear()
        for index, _cluster in enumerate(self.result.clusters):
            list_view.append(ListItem(Static(cluster_label(self.result, index))))
        if self.result.selected_cluster_index is not None and self.result.clusters:
            list_view.index = self.result.selected_cluster_index
        self._set_status("Ready.")

    def _set_status(self, message: str) -> None:
        self.query_one("#status-line", Static).update(message)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id != "cluster-list" or self.result is None:
            return
        if event.list_view.index is None:
            return
        self.refresh_analysis(cluster_index=event.list_view.index + 1)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh":
            self.refresh_analysis(cluster_index=self.selected_cluster_index + 1 if self.selected_cluster_index is not None else None)
            return
        if event.button.id == "clean":
            self.action_clean()
            return
        if event.button.id == "quit":
            self.exit()

    def action_refresh(self) -> None:
        self.refresh_analysis(cluster_index=self.selected_cluster_index + 1 if self.selected_cluster_index is not None else None)

    def action_clean(self) -> None:
        if self.result is None or self.result.selected_cluster is None:
            self._set_status("No selected cluster available.")
            return
        try:
            summary = create_clean_branch(self.result, branch_name=self.branch_name)
        except CleanBranchError as exc:
            self._set_status(f"Clean failed: {exc}")
            return
        self._set_status(
            f"Created {summary.branch_name} from {summary.included_commits} commits / {summary.included_files} files."
        )
        self.refresh_analysis(cluster_index=self.selected_cluster_index + 1 if self.selected_cluster_index is not None else None)


def run_tui(branch_name: str | None = None) -> None:
    PatchflowApp(branch_name=branch_name).run()
