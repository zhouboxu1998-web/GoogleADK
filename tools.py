import logging
from pathlib import Path
from itertools import islice

from typing import Dict, Any

from google.adk.tools import ToolContext

from neo4j_for_adk import graphdb, tool_success, tool_error

from helper import get_neo4j_import_dir


def get_approved_user_goal(tool_context: ToolContext):
    """返回用户的目标，这是一个包含图（Graph）的类型及其描述的字典。"""
    if "approved_user_goal" not in tool_context.state:
        return tool_error("未设置 approved_user_goal。请要求用户明确其目标（图的类型和描述）。")

    user_goal_data = tool_context.state["approved_user_goal"]

    return tool_success("approved_user_goal", user_goal_data)


def get_approved_files(tool_context: ToolContext):
    """返回已获批用于导入的文件。"""
    if "approved_files" not in tool_context.state:
        return tool_error("未设置 approved_files。请要求用户批准推荐的文件。")

    files = tool_context.state["approved_files"]

    return tool_success("approved_files", files)


# 工具：文件采样 (Sample File)
def sample_file(file_path: str) -> dict:
    """对文件进行采样，将其内容作为文本读取。

    将任何文件视为文本，最多读取 100 行。

    参数:
      file_path: 要采样的文件，路径相对于导入目录 (import directory)

    返回:
        dict: 包含内容元数据以及文件采样的字典。
              包含一个 'status' 键（'success' 或 'error'）。
              如果状态为 'success'，则包含一个 'content' 键，值为文本格式的文件内容。
              如果状态为 'error'，则包含一个 'error_message' 键。
    """
    import_dir = Path(get_neo4j_import_dir() or "")

    if not import_dir.exists():
        return tool_error(f"NEO4J_IMPORT_DIR 不存在或未定义: {import_dir}")

    full_path_to_file = import_dir / file_path

    if not full_path_to_file.exists():
        return tool_error(f"导入目录中不存在该文件: {file_path}")

    try:
        # 将所有文件视为文本处理
        with open(full_path_to_file, 'r', encoding='utf-8') as file:
            # 最多读取 100 行
            lines = list(islice(file, 100))
            content = ''.join(lines)
            return tool_success("content", content)

    except Exception as e:
        return tool_error(f"读取或处理文件 {file_path} 时出错: {e}")


### Neo4j 工具 ###
def neo4j_is_ready():
    return graphdb.send_query("RETURN 'Neo4j is Ready!' as message")


def drop_neo4j_indexes() -> Dict[str, Any]:
    """删除 neo4j 图数据库中现有的所有约束 (constraints) 和索引 (indexes)

    返回:
        成功信息或错误信息。
    """
    # 删除所有约束
    list_constraints = graphdb.send_query(
        """SHOW CONSTRAINTS YIELD name"""
    )
    if (list_constraints == "error"):
        return list_constraints
    constraint_names = [row["name"] for row in list_constraints["query_result"]]
    for constraint_name in constraint_names:
        dropped_constraint = graphdb.send_query("""DROP CONSTRAINT $constraint_name""",
                                                {"constraint_name": constraint_name})
        if (dropped_constraint["status"] == "error"):
            return dropped_constraint

    # 删除所有索引
    list_indexes = graphdb.send_query(
        """SHOW INDEXES YIELD name"""
    )
    if (list_indexes == "error"):
        return list_indexes
    index_names = [row["name"] for row in list_indexes["query_result"]]
    for index_name in index_names:
        dropped_index = graphdb.send_query("""DROP INDEX $index_name""", {"index_name": index_name})
        if (dropped_index["status"] == "error"):
            return dropped_index

    return tool_success("message", "Neo4j 的约束和索引已删除。")


def clear_neo4j_data() -> Dict[str, Any]:
    """清除 neo4j 图数据库中的所有数据。

    请谨慎使用！需与用户确认他们清楚此操作将完全重置数据库。

    返回:
        成功信息或错误信息。
    """
    # 首先，分批删除所有节点和关系（每批 10000 行）
    data_removed = graphdb.send_query("""MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 10000 ROWS""")
    if (data_removed["status"] == "error"):
        return data_removed

    return tool_success("message", "Neo4j 图数据库已重置。")


def get_apoc_procedure_names() -> Dict[str, Any]:
    """列出所有 APOC 过程 (procedure) 的名称。
    APOC (Awesome Procedures on Cypher) 是一个扩展 Neo4j 功能的过程和函数库。

    返回:
        成功时返回 APOC 过程名称的列表，失败时返回错误信息。
    """
    cypher = "SHOW PROCEDURES YIELD name WHERE name STARTS WITH 'apoc' RETURN name"

    result = graphdb.send_query(cypher)

    if result["status"] == "error":
        return result
    apoc_procedure_names = [row["name"] for row in result["query_result"]]

    if len(apoc_procedure_names) == 0:
        return tool_error("未找到 APOC 过程。请确保您的 Neo4j 数据库已安装 APOC。")

    return tool_success("apoc_procedure_names", apoc_procedure_names)


def get_apoc_version() -> Dict[str, Any]:
    """获取 Neo4j 数据库中安装的 APOC 版本。

    返回:
        成功时返回 APOC 版本号，失败时返回错误信息。
    """
    cypher = "RETURN apoc.version() AS apoc_version"

    result = graphdb.send_query(cypher)

    if result["status"] == "error":
        return result

    apoc_version = result["query_result"][0]["apoc_version"]

    return tool_success("apoc_version", apoc_version)


def get_neo4j_version() -> Dict[str, Any]:
    """获取 Neo4j 数据库的版本号和版本类型 (edition)。

    """
    cypher = "CALL dbms.components() yield name, versions, edition unwind versions as version return name, version, edition"

    result = graphdb.send_query(cypher)

    if result["status"] == "error":
        return result

    return tool_success("neo4j_version", result["query_result"][0])


def create_uniqueness_constraint(
        label: str,
        unique_property_key: str,
) -> Dict[str, Any]:
    """为节点标签 (label) 和属性键 (property key) 创建唯一性约束。
    唯一性约束可确保不会有两个具有相同标签和属性键的节点拥有相同的值。
    这能提高数据导入的性能以及后续查询的数据完整性。

    参数:
        label: 要为其创建约束的节点标签。
        unique_property_key: 应该具有唯一值的属性键。

    返回:
        包含 'status' 键（'success' 或 'error'）的字典。
        发生错误时，会包含一个 'error_message' 键。
    """
    # 由于 Neo4j 在创建约束时不支持对标签和属性键使用参数化查询，因此这里使用字符串格式化 (f-string)
    constraint_name = f"{label}_{unique_property_key}_constraint"
    query = f"""CREATE CONSTRAINT `{constraint_name}` IF NOT EXISTS
    FOR (n:`{label}`)
    REQUIRE n.`{unique_property_key}` IS UNIQUE"""
    results = graphdb.send_query(query)
    return results


def load_nodes_from_csv(
        source_file: str,
        label: str,
        unique_column_name: str,
        properties: list[str],
) -> Dict[str, Any]:
    """从 CSV 文件批量加载节点"""

    # 根据 unique_column_name（唯一列名）的值进行 MERGE（合并/去重），从 CSV 文件加载节点
    query = f"""LOAD CSV WITH HEADERS FROM "file:///" + $source_file AS row
    CALL (row) {{
        MERGE (n:$($label) {{ {unique_column_name} : row[$unique_column_name] }})
        FOREACH (k IN $properties | SET n[k] = row[k])
    }} IN TRANSACTIONS OF 1000 ROWS
    """

    results = graphdb.send_query(query, {
        "source_file": source_file,
        "label": label,
        "unique_column_name": unique_column_name,
        "properties": properties
    })
    return results


def load_product_nodes() -> Dict[str, Any]:
    """从 products.csv 文件中加载产品 (Product) 节点"""
    return load_nodes_from_csv(
        "products.csv",
        "Product",
        "product_id",
        ["product_name", "price", "description"]
    )