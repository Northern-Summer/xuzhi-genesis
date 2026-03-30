#!/usr/bin/env python3
"""
Equation Parser and Evaluator Generator
方程解析器和求值器生成器

从ETP Lean文件自动生成Python求值器
"""

import re
from typing import Dict, Callable, Optional
from dataclasses import dataclass


@dataclass
class ParsedEquation:
    """解析后的方程"""
    id: int
    left_expr: str
    right_expr: str
    lean_notation: str


class EquationParser:
    """从Lean格式解析方程"""
    
    @staticmethod
    def parse_lean_line(line: str) -> Optional[ParsedEquation]:
        """
        解析单行Lean方程定义
        
        格式: equation N := expression
        或: -- equation N := expression (注释掉的)
        """
        # 去掉注释标记和首尾空格
        line = line.strip()
        if line.startswith('--'):
            line = line[2:].strip()
        
        # 匹配方程定义 - 处理多个空格
        # equation 1  :=  x = x
        pattern = r'equation\s+(\d+)\s*:=\s*(.+)'
        match = re.match(pattern, line)
        
        if not match:
            return None
        
        eq_id = int(match.group(1))
        expr = match.group(2).strip()
        
        # 分割等式两边
        if '=' not in expr:
            return None
        
        parts = expr.split('=', 1)
        left = parts[0].strip()
        right = parts[1].strip()
        
        return ParsedEquation(
            id=eq_id,
            left_expr=left,
            right_expr=right,
            lean_notation=expr
        )
    
    @staticmethod
    def parse_file(filepath: str) -> Dict[int, ParsedEquation]:
        """解析整个Lean文件"""
        equations = {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                eq = EquationParser.parse_lean_line(line)
                if eq:
                    equations[eq.id] = eq
        
        return equations


class EvaluatorGenerator:
    """生成Python求值器代码"""
    
    @staticmethod
    def lean_to_python(expr: str) -> str:
        """
        将Lean表达式转换为Python
        
        Lean: x ◇ y, (x ◇ y) ◇ z
        Python: table[(x, y)], table[(table[(x, y)], z)]
        """
        # 替换操作符 (Unicode diamond to *)
        expr = expr.replace('◇', '*')
        
        # 解析表达式并转换为table访问
        return EvaluatorGenerator._parse_expr(expr)
    
    @staticmethod
    def _parse_expr(expr: str) -> str:
        """递归解析表达式"""
        expr = expr.strip()
        
        # 处理括号
        while expr.startswith('(') and expr.endswith(')'):
            # 检查括号是否匹配
            depth = 0
            match = True
            for i, c in enumerate(expr):
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                if depth == 0 and i < len(expr) - 1:
                    match = False
                    break
            
            if match:
                expr = expr[1:-1].strip()
            else:
                break
        
        # 分割二元操作
        # 找最外层的操作符
        depth = 0
        for i, c in enumerate(expr):
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
            elif c == '*' and depth == 0:
                # 找到操作符
                left = expr[:i].strip()
                right = expr[i+1:].strip()
                
                left_py = EvaluatorGenerator._parse_expr(left)
                right_py = EvaluatorGenerator._parse_expr(right)
                
                return f"table[({left_py}, {right_py})]"
        
        # 不是二元操作，是变量
        return expr
    
    @staticmethod
    def generate_evaluator(eq: ParsedEquation) -> str:
        """为单个方程生成求值器函数"""
        left_py = EvaluatorGenerator.lean_to_python(eq.left_expr)
        right_py = EvaluatorGenerator.lean_to_python(eq.right_expr)
        
        # 确定需要的变量
        variables = set()
        for var in ['x', 'y', 'z', 'w']:
            if var in eq.lean_notation:
                variables.add(var)
        
        var_list = sorted(variables)
        
        # 生成函数
        code = f"""def eq{eq.id}(table, n):
    \"\"\"Equation {eq.id}: {eq.lean_notation}\"\"\"
    for {', '.join(var_list)} in range(n):
        if {left_py} != {right_py}:
            return False
    return True"""
        return code
    
    @staticmethod
    def generate_all_evaluators(equations: Dict[int, ParsedEquation]) -> str:
        """生成所有方程的求值器"""
        lines = [
            "# Auto-generated equation evaluators",
            "# Generated from ETP Lean files",
            "",
            "EQUATION_EVALUATORS = {}",
            "",
        ]
        
        for eq_id in sorted(equations.keys()):
            eq = equations[eq_id]
            func_code = EvaluatorGenerator.generate_evaluator(eq)
            lines.append(func_code)
            lines.append(f"EQUATION_EVALUATORS[{eq_id}] = eq{eq.id}")
            lines.append("")
        
        return '\n'.join(lines)


class EquationEvaluatorLoader:
    """加载和使用方程求值器"""
    
    def __init__(self, equations_file: Optional[str] = None):
        self.evaluators: Dict[int, Callable] = {}
        
        if equations_file:
            self.load_from_file(equations_file)
    
    def load_from_file(self, filepath: str):
        """从Lean文件加载方程"""
        equations = EquationParser.parse_file(filepath)
        
        for eq_id, eq in equations.items():
            # 动态生成并编译求值器
            code = EvaluatorGenerator.generate_evaluator(eq)
            
            # 执行代码定义函数
            local_ns = {}
            exec(code, local_ns)
            
            self.evaluators[eq_id] = local_ns[f'eq{eq_id}']
    
    def evaluate(self, eq_id: int, table: Dict, n: int) -> Optional[bool]:
        """评估方程在magma上是否成立"""
        if eq_id not in self.evaluators:
            return None
        
        try:
            return self.evaluators[eq_id](table, n)
        except Exception:
            return None
    
    def get_supported_equations(self) -> list:
        """获取支持的方程ID列表"""
        return sorted(self.evaluators.keys())


if __name__ == "__main__":
    # 测试解析器
    test_lines = [
        "equation 1 := x = x",
        "equation 3 := x = x ◇ x",
        "equation 65 := x = y ◇ (x ◇ (y ◇ x))",
        "equation 359 := x ◇ x = (x ◇ x) ◇ x",
    ]
    
    print("Testing Equation Parser:")
    print("=" * 60)
    
    for line in test_lines:
        print(f"\nInput: {line}")
        eq = EquationParser.parse_lean_line(line)
        if eq:
            print(f"  Parsed: Eq {eq.id}")
            print(f"  Left: {eq.left_expr}")
            print(f"  Right: {eq.right_expr}")
            code = EvaluatorGenerator.generate_evaluator(eq)
            print(f"  Generated code:\n{code}")
        else:
            print("  FAILED TO PARSE")
        print("-" * 40)
    
    # Test on real file
    print("\n\nTesting on real ETP file:")
    print("=" * 60)
    
    lean_file = '/home/summer/xuzhi_genesis/centers/mathematics/math_ai4s/etp_work/equational_theories/equational_theories/Equations/Basic.lean'
    equations = EquationParser.parse_file(lean_file)
    
    print(f"Found {len(equations)} equations in Basic.lean")
    for eq_id in sorted(equations.keys())[:5]:
        eq = equations[eq_id]
        print(f"  Eq {eq.id}: {eq.lean_notation[:50]}...")
