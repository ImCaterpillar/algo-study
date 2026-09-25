def analyze_problem_difficulty(problem_description: str, examples: list, constraints: str) -> dict:
    """分析题目难度"""
    length = len(problem_description)
    example_count = len(examples)
    
    difficulty_score = 0
    factors = []
    
    if "hard" in problem_description.lower() or "困难" in problem_description:
        difficulty_score += 30
        factors.append("题目描述包含困难标识")
    if "medium" in problem_description.lower() or "中等" in problem_description:
        difficulty_score += 20
        factors.append("题目描述包含中等标识")
    
    if length > 500:
        difficulty_score += 15
        factors.append("题目描述较长")
    elif length > 300:
        difficulty_score += 10
        factors.append("题目描述中等长度")
    
    if "O(n)" in constraints or "线性" in constraints:
        difficulty_score += 5
    if "O(log n)" in constraints or "对数" in constraints:
        difficulty_score += 10
    if "O(n log n)" in constraints:
        difficulty_score += 15
    if "O(n²)" in constraints or "平方" in constraints:
        difficulty_score += 5
    if "O(2ⁿ)" in constraints or "指数" in constraints:
        difficulty_score += 25
        factors.append("指数级复杂度约束")
    
    if example_count >= 3:
        difficulty_score += 5
    
    if difficulty_score >= 60:
        difficulty = "Hard"
    elif difficulty_score >= 35:
        difficulty = "Medium"
    else:
        difficulty = "Easy"
    
    return {
        "predicted_difficulty": difficulty,
        "confidence": min(0.8 + (difficulty_score % 20) / 100, 0.95),
        "difficulty_score": difficulty_score,
        "factors": factors,
        "suggestion": get_difficulty_suggestion(difficulty),
    }

def get_difficulty_suggestion(difficulty: str) -> str:
    """根据难度给出建议"""
    suggestions = {
        "Easy": "这道题难度较低，适合快速练习以巩固基础概念。建议在15分钟内完成。",
        "Medium": "这道题难度适中，需要仔细思考解题思路。建议先分析题目模式，再动手实现。",
        "Hard": "这道题难度较高，建议先复习相关的数据结构和算法。可以尝试分阶段完成：先理解题意，再设计算法，最后实现。",
    }
    return suggestions.get(difficulty, "")

def generate_problem_hints(problem_description: str, examples: list, tags: list) -> list:
    """生成解题思路提示"""
    hints = []
    
    if "array" in [t.lower() for t in tags] or "数组" in tags:
        hints.append("考虑使用双指针技巧，特别是当需要在数组两端同时操作时。")
        hints.append("滑动窗口技术适用于处理子数组相关问题。")
    
    if "string" in [t.lower() for t in tags] or "字符串" in tags:
        hints.append("考虑使用栈来处理括号匹配或回文判断问题。")
        hints.append("双指针法可以从两端向中间逼近解决某些字符串问题。")
    
    if "hash" in [t.lower() for t in tags] or "哈希" in tags or "map" in [t.lower() for t in tags]:
        hints.append("哈希表可以用于快速查找和计数，时间复杂度为O(1)。")
        hints.append("考虑使用字典来存储频率计数或映射关系。")
    
    if "dp" in [t.lower() for t in tags] or "动态" in tags:
        hints.append("动态规划问题需要定义状态和状态转移方程。")
        hints.append("先尝试找出递推关系，再考虑空间优化。")
    
    if "tree" in [t.lower() for t in tags] or "树" in tags:
        hints.append("二叉树问题通常可以用递归或迭代方式解决。")
        hints.append("考虑使用深度优先搜索(DFS)或广度优先搜索(BFS)。")
    
    if "graph" in [t.lower() for t in tags] or "图" in tags:
        hints.append("图遍历可以使用BFS或DFS，注意处理环的问题。")
        hints.append("考虑使用visited数组或集合来避免重复访问。")
    
    if "binary search" in [t.lower() for t in tags] or "二分" in tags:
        hints.append("二分查找需要有序数组，时间复杂度为O(log n)。")
        hints.append("注意边界条件，特别是low和high的更新方式。")
    
    if "two pointers" in [t.lower() for t in tags] or "双指针" in tags:
        hints.append("双指针可以从两端或同向移动，适用于有序数组。")
    
    if "stack" in [t.lower() for t in tags] or "栈" in tags:
        hints.append("栈适用于需要后进先出顺序处理的问题。")
    
    if "greedy" in [t.lower() for t in tags] or "贪心" in tags:
        hints.append("贪心算法需要找到局部最优解，证明其能得到全局最优。")
    
    if "backtracking" in [t.lower() for t in tags] or "回溯" in tags:
        hints.append("回溯算法需要尝试所有可能的组合，注意剪枝优化。")
    
    if len(hints) == 0:
        hints.append("仔细阅读题目，理解输入输出要求。")
        hints.append("尝试举几个例子来理解问题规律。")
        hints.append("考虑使用暴力解法作为起点，再优化时间复杂度。")
    
    return hints[:5]

def review_code(code: str, language: str, problem_tags: list) -> dict:
    """代码审查建议"""
    suggestions = []
    warnings = []
    
    lines = code.split('\n')
    line_count = len(lines)
    
    if line_count > 100:
        suggestions.append("代码较长，考虑拆分函数以提高可读性。")
    
    if code.count('print') > 5 and language == 'python':
        suggestions.append("存在较多print语句，考虑使用日志替代或移除调试代码。")
    
    if code.count('console.log') > 5 and language == 'javascript':
        suggestions.append("存在较多console.log语句，考虑使用调试工具替代。")
    
    if "for " in code and "while " in code:
        suggestions.append("代码同时使用for和while循环，保持一致性会更好。")
    
    if code.count('if') > 10:
        suggestions.append("条件判断较多，考虑使用字典映射或多态来简化。")
    
    if 'TODO' in code or 'FIXME' in code:
        warnings.append("代码中包含未完成的标记(TODO/FIXME)，建议完成或移除。")
    
    if 'hardcode' in code.lower() or 'magic number' in code.lower():
        warnings.append("代码中可能存在硬编码值，建议定义常量。")
    
    if "array" in [t.lower() for t in problem_tags]:
        if code.count('[') > code.count(']') or code.count(']') > code.count('['):
            warnings.append("数组括号可能不匹配，建议检查。")
    
    if "dp" in [t.lower() for t in problem_tags]:
        if 'dp' not in code.lower() and 'dp[' not in code.lower():
            suggestions.append("动态规划问题建议使用dp数组来存储中间结果。")
    
    if "recursion" in [t.lower() for t in problem_tags] or "tree" in [t.lower() for t in problem_tags]:
        if 'def ' not in code and language == 'python':
            suggestions.append("递归问题建议使用函数来实现。")
        if 'function ' not in code and '=>' not in code and language == 'javascript':
            suggestions.append("递归问题建议使用函数来实现。")
    
    if code.count('else') < code.count('if') - 1:
        suggestions.append("部分if语句缺少else分支，考虑完整性。")
    
    if code.count('try') != code.count('catch') and language != 'python':
        suggestions.append("try-catch块可能不完整，建议检查。")
    
    if len(suggestions) == 0 and len(warnings) == 0:
        suggestions.append("代码结构良好，建议进行测试用例验证。")
    
    return {
        "suggestions": suggestions[:6],
        "warnings": warnings[:3],
        "overall_rating": get_code_rating(len(suggestions), len(warnings)),
    }

def get_code_rating(suggestion_count: int, warning_count: int) -> str:
    """根据建议和警告数量给出评分"""
    if warning_count == 0 and suggestion_count <= 2:
        return "优秀"
    elif warning_count <= 1 and suggestion_count <= 4:
        return "良好"
    elif warning_count <= 2 and suggestion_count <= 6:
        return "中等"
    else:
        return "需要改进"

def generate_explanation(problem_description: str, tags: list) -> str:
    """生成题目讲解"""
    explanations = []
    
    if "array" in [t.lower() for t in tags]:
        explanations.append("数组是最基础的数据结构之一，支持O(1)的随机访问。")
    
    if "hash" in [t.lower() for t in tags]:
        explanations.append("哈希表通过哈希函数将键映射到存储位置，实现快速查找。")
    
    if "dp" in [t.lower() for t in tags]:
        explanations.append("动态规划是一种将复杂问题分解为子问题的算法思想。")
    
    if "tree" in [t.lower() for t in tags]:
        explanations.append("树是一种层次结构，每个节点可以有多个子节点。")
    
    if "graph" in [t.lower() for t in tags]:
        explanations.append("图由节点和边组成，用于表示对象之间的关系。")
    
    if "binary search" in [t.lower() for t in tags]:
        explanations.append("二分查找是一种高效的搜索算法，时间复杂度为O(log n)。")
    
    if len(explanations) == 0:
        return "这道题目涉及以下知识点：" + ", ".join(tags)
    
    return "\n".join(explanations)