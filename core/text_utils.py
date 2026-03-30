"""
文本处理工具模块
提供 LaTeX 格式清理等功能
"""

import re


def clean_latex(text: str) -> str:
    """
    清理 LaTeX 格式标记，转换为可读纯文本
    
    处理内容包括:
    - \textbf{content} -> content
    - \textit{content} -> content
    - \mathbb{R} -> R
    - $...$ 数学模式 -> 纯文本
    - \cite{...} -> 移除
    - 希腊字母 -> Unicode 字符
    - 上下标 -> Unicode 字符
    """
    if not text:
        return text
    
    # 保存原始文本用于调试
    original = text
    
    # 0. 先处理数学模式 $...$ 中的内容，在移除 $ 之前处理其中的 LaTeX 命令
    # 处理数学模式中的 \mathbf{...}, \mathbb{...} 等命令
    math_commands = ['mathbf', 'mathit', 'mathrm', 'mathbb', 'mathcal', 'mathfrak', 'boldsymbol']
    
    def process_math_content(match):
        """处理数学模式中的内容"""
        content = match.group(1)
        # 处理数学模式中的 LaTeX 命令
        for cmd in math_commands:
            content = re.sub(r'\\' + cmd + r'\{([^}]*)\}', r'\1', content)
        # 处理数学符号
        content = content.replace(r'\neq', '≠')
        content = content.replace(r'\leq', '≤')
        content = content.replace(r'\geq', '≥')
        content = content.replace(r'\times', '×')
        content = content.replace(r'\cdot', '·')
        content = content.replace(r'\approx', '≈')
        content = content.replace(r'\rightarrow', '→')
        content = content.replace(r'\leftarrow', '←')
        content = content.replace(r'\Rightarrow', '⇒')
        content = content.replace(r'\Leftarrow', '⇐')
        content = content.replace(r'\in', '∈')
        content = content.replace(r'\subset', '⊂')
        content = content.replace(r'\cup', '∪')
        content = content.replace(r'\cap', '∩')
        content = content.replace(r'\sum', '∑')
        content = content.replace(r'\prod', '∏')
        content = content.replace(r'\int', '∫')
        content = content.replace(r'\pm', '±')
        content = content.replace(r'\infty', '∞')
        content = content.replace(r'\alpha', 'α')
        content = content.replace(r'\beta', 'β')
        content = content.replace(r'\gamma', 'γ')
        content = content.replace(r'\delta', 'δ')
        content = content.replace(r'\lambda', 'λ')
        content = content.replace(r'\mu', 'μ')
        content = content.replace(r'\pi', 'π')
        content = content.replace(r'\sigma', 'σ')
        content = content.replace(r'\theta', 'θ')
        content = content.replace(r'\phi', 'φ')
        content = content.replace(r'\omega', 'ω')
        # 移除残余的反斜杠命令
        content = re.sub(r'\\[a-zA-Z]+', '', content)
        return content
    
    # 处理 $...$ 数学模式
    text = re.sub(r'\$([^$]+)\$', process_math_content, text)
    
    # 1. 移除 LaTeX 命令并保留内容: \textbf{content} -> content
    # 处理嵌套花括号的情况，使用循环直到没有变化
    latex_commands_with_content = [
        'textbf', 'textit', 'textrm', 'texttt', 'textsf', 'textsc',
        'mathbf', 'mathit', 'mathrm', 'mathbb', 'mathcal', 'mathfrak',
        'boldsymbol', 'emph', 'underline', 'overline',
        'hat', 'tilde', 'bar', 'vec', 'dot', 'ddot',
    ]
    
    for cmd in latex_commands_with_content:
        # 处理简单花括号: \cmd{content}
        pattern = r'\\' + cmd + r'\{([^}]*)\}'
        text = re.sub(pattern, r'\1', text)
    
    # 2. 移除无内容的 LaTeX 命令: \cite{...}, \ref{...}, \label{...}
    remove_commands = ['cite', 'ref', 'label', 'eqref', 'footnote', 'bibitem']
    for cmd in remove_commands:
        # 移除命令及其参数
        pattern = r'\\' + cmd + r'\{[^}]*\}'
        text = re.sub(pattern, '', text)
        # 处理带方括号的变体: \cite[...]{...}
        pattern = r'\\' + cmd + r'\[[^\]]*\]\{[^}]*\}'
        text = re.sub(pattern, '', text)
    
    # 3. 常见希腊字母替换
    greek = {
        'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ',
        'epsilon': 'ε', 'varepsilon': 'ε', 'zeta': 'ζ', 'eta': 'η', 
        'theta': 'θ', 'vartheta': 'θ', 'lambda': 'λ', 'mu': 'μ', 
        'nu': 'ν', 'pi': 'π', 'varpi': 'π', 'rho': 'ρ', 'sigma': 'σ',
        'varsigma': 'ς', 'tau': 'τ', 'phi': 'φ', 'varphi': 'φ',
        'chi': 'χ', 'psi': 'ψ', 'omega': 'ω',
        'Alpha': 'Α', 'Beta': 'Β', 'Gamma': 'Γ', 'Delta': 'Δ',
        'Theta': 'Θ', 'Lambda': 'Λ', 'Pi': 'Π', 'Sigma': 'Σ',
        'Omega': 'Ω', 'Phi': 'Φ', 'Psi': 'Ψ',
    }
    for name, symbol in greek.items():
        # 确保命令后面不是字母（避免匹配部分命令）
        text = re.sub(r'\\' + name + r'(?![a-zA-Z])', symbol, text)
    
    # 4. 常见数学符号
    symbols = {
        r'\times': '×', r'\cdot': '·', r'\leq': '≤', r'\geq': '≥',
        r'\neq': '≠', r'\approx': '≈', r'\infty': '∞',
        r'\rightarrow': '→', r'\leftarrow': '←', r'\Rightarrow': '⇒',
        r'\Leftarrow': '⇐', r'\in': '∈', r'\subset': '⊂', 
        r'\cup': '∪', r'\cap': '∩', r'\setminus': '\\',
        r'\sum': '∑', r'\prod': '∏', r'\int': '∫',
        r'\pm': '±', r'\mp': '∓', r'\ldots': '...', r'\cdots': '...',
        r'\partial': '∂', r'\nabla': '∇', r'\forall': '∀', r'\exists': '∃',
        r'\emptyset': '∅', r'\sqrt': '√',
    }
    for latex, symbol in symbols.items():
        text = text.replace(latex, symbol)
    
    # 5. 上标: ^{2} -> ², ^2 -> ²
    superscripts = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        'n': 'ⁿ', 'i': 'ⁱ', '+': '⁺', '-': '⁻',
    }
    # 先处理花括号形式: ^{...}
    text = re.sub(r'\^\{([^}]+)\}', lambda m: _convert_superscript(m.group(1), superscripts), text)
    # 再处理单字符形式: ^x
    for char, sup in superscripts.items():
        text = re.sub(r'\^' + re.escape(char) + r'(?![a-zA-Z0-9])', sup, text)
    
    # 6. 下标: _{content} -> content
    subscripts = {
        '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
        '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
        'i': 'ᵢ', 'j': 'ⱼ', 'k': 'ₖ', 'n': 'ₙ',
    }
    # 先处理花括号形式: _{...}
    text = re.sub(r'_\{([^}]+)\}', lambda m: _convert_subscript(m.group(1), subscripts), text)
    # 再处理单字符形式
    for char, sub in subscripts.items():
        text = re.sub(r'_' + re.escape(char) + r'(?![a-zA-Z0-9])', sub, text)
    
    # 7. 处理 $...$ 数学模式，移除 $ 符号但保留内容
    # 先处理简单数学模式
    text = re.sub(r'\$([^$]+)\$', lambda m: _process_math_mode(m.group(1)), text)
    
    # 8. 清理残余的反斜杠命令
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)  # \anycommand{content} -> content
    text = re.sub(r'\\[a-zA-Z]+', '', text)  # \anycommand -> 移除
    
    # 9. 清理多余的花括号
    text = text.replace('{', '').replace('}', '')
    
    # 10. 清理 LaTeX 特殊字符
    text = text.replace('~', ' ')  # 不换行空格
    text = text.replace('\\', ' ')  # 强制换行
    text = text.replace('\%', '%')  # 转义百分号
    text = text.replace('\&', '&')  # 转义&
    text = text.replace('\$', '$')  # 转义$
    text = text.replace('\#', '#')  # 转义#
    text = text.replace('\_', '_')  # 转义下划线
    text = text.replace('\{', '{')  # 转义{
    text = text.replace('\}', '}')  # 转义}
    text = text.replace('\\', '')   # 残余反斜杠
    
    # 11. 清理多余空格
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text


def _convert_superscript(content: str, mapping: dict) -> str:
    """将内容转换为上标 Unicode 字符"""
    result = ''
    for char in content:
        result += mapping.get(char, char)
    return result


def _convert_subscript(content: str, mapping: dict) -> str:
    """将内容转换为下标 Unicode 字符"""
    result = ''
    for char in content:
        result += mapping.get(char, char)
    return result


def _process_math_mode(content: str) -> str:
    """处理数学模式内容，移除残余 LaTeX 命令"""
    # 移除数学模式中的残余命令
    content = re.sub(r'\\[a-zA-Z]+', '', content)
    return content
