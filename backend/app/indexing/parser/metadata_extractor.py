from __future__ import annotations

from dataclasses import dataclass

from tree_sitter import Node

from app.indexing.parser.ast_utils import ASTUtils, NodeLocation
from app.indexing.parser.tree_sitter_parser import ParsedSource


@dataclass(frozen=True)
class CodeMetadata:
    """
    Metadata extracted from a source file's AST.
    """

    node_type: str
    name: str | None
    location: NodeLocation
    source: str


@dataclass(frozen=True)
class FileMetadata:
    """
    Semantic metadata extracted from a parsed source file.
    """

    language: str
    classes: tuple[CodeMetadata, ...]
    functions: tuple[CodeMetadata, ...]
    methods: tuple[CodeMetadata, ...]
    imports: tuple[CodeMetadata, ...]
    has_syntax_errors: bool


class MetadataExtractor:
    """
    Extracts high-level code metadata from Tree-sitter syntax trees.

    The extractor is intentionally language-aware only through a
    configurable node-type registry. Tree-sitter traversal itself is
    delegated to ASTUtils.
    """

    NODE_TYPES: dict[str, dict[str, frozenset[str]]] = {
        "python": {
            "class": frozenset(
                {
                    "class_definition",
                }
            ),
            "function": frozenset(
                {
                    "function_definition",
                }
            ),
            "method": frozenset(
                {
                    "function_definition",
                }
            ),
            "import": frozenset(
                {
                    "import_statement",
                    "import_from_statement",
                }
            ),
        },
        "javascript": {
            "class": frozenset(
                {
                    "class_declaration",
                }
            ),
            "function": frozenset(
                {
                    "function_declaration",
                    "function",
                    "arrow_function",
                }
            ),
            "method": frozenset(
                {
                    "method_definition",
                }
            ),
            "import": frozenset(
                {
                    "import_statement",
                }
            ),
        },
        "typescript": {
            "class": frozenset(
                {
                    "class_declaration",
                    "class",
                }
            ),
            "function": frozenset(
                {
                    "function_declaration",
                    "function",
                    "arrow_function",
                }
            ),
            "method": frozenset(
                {
                    "method_definition",
                }
            ),
            "import": frozenset(
                {
                    "import_statement",
                }
            ),
        },
        "java": {
            "class": frozenset(
                {
                    "class_declaration",
                    "interface_declaration",
                    "enum_declaration",
                }
            ),
            "function": frozenset(),
            "method": frozenset(
                {
                    "method_declaration",
                }
            ),
            "import": frozenset(
                {
                    "import_declaration",
                }
            ),
        },
        "c": {
            "class": frozenset(),
            "function": frozenset(
                {
                    "function_definition",
                }
            ),
            "method": frozenset(),
            "import": frozenset(
                {
                    "preproc_include",
                }
            ),
        },
        "cpp": {
            "class": frozenset(
                {
                    "class_specifier",
                    "struct_specifier",
                }
            ),
            "function": frozenset(
                {
                    "function_definition",
                }
            ),
            "method": frozenset(
                {
                    "function_definition",
                }
            ),
            "import": frozenset(
                {
                    "preproc_include",
                }
            ),
        },
        "csharp": {
            "class": frozenset(
                {
                    "class_declaration",
                    "struct_declaration",
                    "interface_declaration",
                }
            ),
            "function": frozenset(),
            "method": frozenset(
                {
                    "method_declaration",
                }
            ),
            "import": frozenset(
                {
                    "using_directive",
                }
            ),
        },
        "go": {
            "class": frozenset(),
            "function": frozenset(
                {
                    "function_declaration",
                }
            ),
            "method": frozenset(
                {
                    "method_declaration",
                }
            ),
            "import": frozenset(
                {
                    "import_declaration",
                }
            ),
        },
        "rust": {
            "class": frozenset(),
            "function": frozenset(
                {
                    "function_item",
                }
            ),
            "method": frozenset(
                {
                    "function_item",
                }
            ),
            "import": frozenset(
                {
                    "use_declaration",
                }
            ),
        },
        "ruby": {
            "class": frozenset(
                {
                    "class",
                }
            ),
            "function": frozenset(
                {
                    "method",
                }
            ),
            "method": frozenset(
                {
                    "method",
                }
            ),
            "import": frozenset(
                {
                    "call",
                }
            ),
        },
        "php": {
            "class": frozenset(
                {
                    "class_declaration",
                    "interface_declaration",
                    "trait_declaration",
                }
            ),
            "function": frozenset(
                {
                    "function_definition",
                }
            ),
            "method": frozenset(
                {
                    "method_declaration",
                }
            ),
            "import": frozenset(
                {
                    "namespace_use_declaration",
                }
            ),
        },
        "kotlin": {
            "class": frozenset(
                {
                    "class_declaration",
                    "object_declaration",
                }
            ),
            "function": frozenset(
                {
                    "function_declaration",
                }
            ),
            "method": frozenset(
                {
                    "function_declaration",
                }
            ),
            "import": frozenset(
                {
                    "import_header",
                }
            ),
        },
        "swift": {
            "class": frozenset(
                {
                    "class_declaration",
                    "struct_declaration",
                    "protocol_declaration",
                }
            ),
            "function": frozenset(
                {
                    "function_declaration",
                }
            ),
            "method": frozenset(
                {
                    "function_declaration",
                }
            ),
            "import": frozenset(
                {
                    "import_declaration",
                }
            ),
        },
    }

    def extract(
        self,
        parsed_source: ParsedSource,
    ) -> FileMetadata:
        """
        Extract semantic metadata from a parsed source file.
        """

        language = parsed_source.language.lower()

        node_types = self.NODE_TYPES.get(
            language,
            {},
        )

        root = parsed_source.tree.root_node

        source_bytes = parsed_source.source_code.encode("utf-8")

        classes = self._extract_nodes(
            root=root,
            node_types=node_types.get(
                "class",
                frozenset(),
            ),
            source_bytes=source_bytes,
        )

        functions = self._extract_nodes(
            root=root,
            node_types=node_types.get(
                "function",
                frozenset(),
            ),
            source_bytes=source_bytes,
            category="function",
            class_node_types=node_types.get("class",frozenset())
            
        )

        methods = self._extract_nodes(
            root=root,
            node_types=node_types.get(
                "method",
                frozenset(),
            ),
            source_bytes=source_bytes,
            category="method",
            class_node_types=node_types.get("class",frozenset())
        )

        imports = self._extract_nodes(
            root=root,
            node_types=node_types.get(
                "import",
                frozenset(),
            ),
            source_bytes=source_bytes,
        )

        return FileMetadata(
            language=parsed_source.language,
            classes=tuple(classes),
            functions=tuple(functions),
            methods=tuple(methods),
            imports=tuple(imports),
            has_syntax_errors=ASTUtils.has_error(root),
        )

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_nodes(
        root: Node,
        node_types: frozenset[str],
        source_bytes: bytes,
        category: str | None = None,
        class_node_types: frozenset[str] | None = None
    ) -> list[CodeMetadata]:
        """
        Extract metadata for all matching nodes.
        """

        if not node_types:
            return []

        nodes = ASTUtils.find_nodes_by_type(
            node=root,
            node_types=node_types,
        )

        if category == "function":
            nodes = [
                node
                for node in nodes
                if not MetadataExtractor._is_method_node(node,class_node_types)
            ]

        elif category == "method":
            nodes = [
                node
                for node in nodes
                if MetadataExtractor._is_method_node(node,class_node_types)
            ]

        return [
            MetadataExtractor._build_metadata(
                node=node,
                source_bytes=source_bytes,
            )
            for node in nodes
        ]
    
    @staticmethod
    def _is_method_node(
        node: Node,
        class_node_types: frozenset[str],
    ) -> bool:
        parent = node.parent

        while parent is not None:
            if parent.type in class_node_types:
                return True

            parent = parent.parent

        return False

    @staticmethod
    def _build_metadata(
        node: Node,
        source_bytes: bytes,
    ) -> CodeMetadata:
        """
        Convert an AST node into application-level metadata.
        """

        name = MetadataExtractor._extract_name(node)

        location = ASTUtils.get_location(node)

        source = ASTUtils.get_node_text(
            node=node,
            source_bytes=source_bytes,
        )

        return CodeMetadata(
            node_type=node.type,
            name=name,
            location=location,
            source=source,
        )

    # ------------------------------------------------------------------
    # Name extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_name(
        node: Node,
    ) -> str | None:
        """
        Extract a semantic name from common Tree-sitter nodes.

        Tree-sitter grammars differ in their field names, so several
        common fields are checked in order.
        """

        for field_name in (
            "name",
            "declarator",
            "left",
        ):
            child = ASTUtils.get_child_by_field(
                node=node,
                field_name=field_name,
            )

            if child is None:
                continue

            if child.type in {
                "identifier",
                "type_identifier",
                "property_identifier",
                "field_identifier",
                "namespace_identifier",
            }:
                return child.text.decode(
                    "utf-8",
                    errors="replace",
                )

            nested_identifier = MetadataExtractor._find_identifier(child)

            if nested_identifier is not None:
                return nested_identifier

        return None

    @staticmethod
    def _find_identifier(
        node: Node,
    ) -> str | None:
        """
        Recursively find the first identifier-like node.
        """

        identifier_types = {
            "identifier",
            "type_identifier",
            "property_identifier",
            "field_identifier",
            "namespace_identifier",
        }

        if node.type in identifier_types:
            return node.text.decode(
                "utf-8",
                errors="replace",
            )

        for child in node.children:
            result = MetadataExtractor._find_identifier(child)

            if result is not None:
                return result

        return None
