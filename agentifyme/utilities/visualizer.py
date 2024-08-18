import networkx as nx
from pyvis.network import Network

from agentifyme.tasks import TaskConfig
from agentifyme.workflows import WorkflowConfig


def get_metadata(func):
    if hasattr(func, "__agentifyme_metadata"):
        return func.__agentifyme_metadata
    elif hasattr(func, "__wrapped__"):
        return get_metadata(func.__wrapped__)
    else:
        return None


def get_config(name):
    workflow = WorkflowConfig.get(name)
    if workflow:
        return workflow, "workflow"
    task = TaskConfig.get(name)
    if task:
        return task, "task"
    print(f"Warning: Could not find {name} in WorkflowConfig or TaskConfig registry")
    return None, None


class WorkflowVisualizer:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.net = Network(height="750px", width="100%", directed=True, notebook=True)
        self.processed_nodes = set()

    def add_node(self, node_id: str, node_type: str, label: str, title: str):
        color = "#97c2fc" if node_type == "workflow" else "#ffaa00"
        shape = "box" if node_type == "workflow" else "ellipse"
        self.graph.add_node(node_id, label=label, title=title, color=color, shape=shape)

    def add_edge(self, source: str, target: str, label: str):
        self.graph.add_edge(source, target, label=label)

    def create_graph(self, top_level_func_name):
        config, node_type = get_config(top_level_func_name)
        if config:
            self.process_node(config.name, config, node_type)

    def process_node(self, node_name, config, node_type, parent=None):
        if node_name in self.processed_nodes:
            if parent:
                self.add_edge(parent, node_name, "")
            return

        self.processed_nodes.add(node_name)

        metadata = get_metadata(config.func)
        if not metadata:
            print(f"Warning: No metadata found for {node_name}")
            return

        label = f"{node_name}\n[{node_type[0].upper()}]"
        title = f"Type: {node_type}\n"
        title += f"Description: {metadata.get('description', 'N/A')}\n"
        title += f"Input: {metadata.get('input_parameters', 'N/A')}\n"
        title += f"Output: {metadata.get('output_parameters', 'N/A')}\n"
        if "objective" in metadata:
            title += f"Objective: {metadata['objective']}\n"
        if "instructions" in metadata:
            title += f"Instructions: {metadata['instructions']}\n"

        self.add_node(node_name, node_type, label, title)

        if parent:
            self.add_edge(parent, node_name, "")

        for nested_call in metadata.get("nested_calls", []):
            nested_config, nested_type = get_config(nested_call)
            if nested_config:
                self.process_node(nested_call, nested_config, nested_type, node_name)

    def visualize(self, filename: str = "workflow_visualization.html"):
        self.net.from_nx(self.graph)
        self.net.set_edge_smooth("dynamic")
        self.net.show_buttons(filter_=["physics"])
        self.net.show(filename)
