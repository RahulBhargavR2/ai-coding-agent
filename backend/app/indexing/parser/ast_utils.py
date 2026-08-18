from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from tree_sitter import Node


@dataclass(frozen=True)
class NodeLocation:
    """
    Represents the source-code location of an AST node.
    """

    start_line: int
    start_column: int
    end_line: int
    end_column: int


class ASTUtils:
    """
    Utility functions for working with Tree-sitter AST nodes.

    This class contains only low-level AST operations.

    It does not:
    - Determine semantic meaning of nodes.
    - Extract classes/functions/modules.
    - Create chunks.
    - Persist data.
    """

    # ------------------------------------------------------------------
    # Traversal
    # ------------------------------------------------------------------

    @staticmethod
    def walk(
        node: Node,
    ) -> Iterator[Node]:
        """
        Traverse an AST depth-first.

        The root node is included in the traversal.
        """

        yield node

        for child in node.children:
            yield from ASTUtils.walk(child)

    @staticmethod
    def walk_named(
        node: Node,
    ) -> Iterator[Node]:
        """
        Traverse only named AST nodes.

        Named nodes generally represent meaningful syntactic
        constructs rather than punctuation or anonymous tokens.
        """

        if node.is_named:
            yield node

        for child in node.children:
            yield from ASTUtils.walk_named(child)

    # ------------------------------------------------------------------
    # Node search
    # ------------------------------------------------------------------

    @staticmethod
    def find_nodes_by_type(
        node: Node,
        node_types: set[str] | frozenset[str],
    ) -> list[Node]:
        """
        Find all AST nodes whose type matches one of the supplied types.
        """

        return [
            current for current in ASTUtils.walk(node) if current.type in node_types
        ]

    @staticmethod
    def find_first_node_by_type(
        node: Node,
        node_types: set[str] | frozenset[str],
    ) -> Node | None:
        """
        Find the first AST node matching one of the supplied types.
        """

        for current in ASTUtils.walk(node):
            if current.type in node_types:
                return current

        return None

    # ------------------------------------------------------------------
    # Node text
    # ------------------------------------------------------------------

    @staticmethod
    def get_node_text(
        node: Node,
        source_bytes: bytes,
    ) -> str:
        """
        Extract the exact source text represented by an AST node.
        """

        return source_bytes[node.start_byte : node.end_byte].decode(
            "utf-8",
            errors="replace",
        )

    # ------------------------------------------------------------------
    # Node location
    # ------------------------------------------------------------------

    @staticmethod
    def get_location(
        node: Node,
    ) -> NodeLocation:
        """
        Return the source location of an AST node.

        Tree-sitter uses zero-based line and column numbers internally.
        This method converts them to one-based line numbers and columns
        for easier use by application-level metadata.
        """

        return NodeLocation(
            start_line=node.start_point.row + 1,
            start_column=node.start_point.column + 1,
            end_line=node.end_point.row + 1,
            end_column=node.end_point.column + 1,
        )

    # ------------------------------------------------------------------
    # Children
    # ------------------------------------------------------------------

    @staticmethod
    def get_named_children(
        node: Node,
    ) -> list[Node]:
        """
        Return the named children of an AST node.
        """

        return [child for child in node.children if child.is_named]

    @staticmethod
    def get_child_by_field(
        node: Node,
        field_name: str,
    ) -> Node | None:
        """
        Retrieve a child node using Tree-sitter's field name.
        """

        return node.child_by_field_name(field_name)

    # ------------------------------------------------------------------
    # Node properties
    # ------------------------------------------------------------------

    @staticmethod
    def is_named(
        node: Node,
    ) -> bool:
        """
        Determine whether a node is a named AST node.
        """

        return node.is_named

    @staticmethod
    def is_error(
        node: Node,
    ) -> bool:
        """
        Determine whether a node represents a Tree-sitter parse error.
        """

        return node.is_error

    @staticmethod
    def has_error(
        node: Node,
    ) -> bool:
        """
        Determine whether an AST subtree contains a parse error.
        """

        if node.has_error:
            return True

        return any(ASTUtils.has_error(child) for child in node.children)
