"""
Document comparison and diff utilities.
"""
import difflib
from .file_handlers import extract_text_content, get_file_type


def text_diff(text1, text2):
    """Generate a line-by-line diff between two text strings."""
    lines1 = text1.splitlines(keepends=True) if text1 else []
    lines2 = text2.splitlines(keepends=True) if text2 else []
    
    differ = difflib.Differ()
    diff = list(differ.compare(lines1, lines2))
    
    result = []
    for line in diff:
        if line.startswith('+ '):
            result.append({'type': 'added', 'content': line[2:]})
        elif line.startswith('- '):
            result.append({'type': 'removed', 'content': line[2:]})
        elif line.startswith('  '):
            result.append({'type': 'unchanged', 'content': line[2:]})
    
    return result


def html_diff(text1, text2):
    """Generate an HTML diff between two text strings."""
    lines1 = text1.splitlines() if text1 else []
    lines2 = text2.splitlines() if text2 else []
    
    differ = difflib.HtmlDiff(wrapcolumn=80)
    return differ.make_table(lines1, lines2, fromdesc='Previous Version', todesc='New Version')


def unified_diff(text1, text2, from_name='v1', to_name='v2'):
    """Generate a unified diff."""
    lines1 = text1.splitlines(keepends=True) if text1 else []
    lines2 = text2.splitlines(keepends=True) if text2 else []
    
    diff = difflib.unified_diff(lines1, lines2, fromfile=from_name, tofile=to_name)
    return ''.join(diff)


def side_by_side_diff(text1, text2):
    """Generate side-by-side comparison data."""
    lines1 = text1.splitlines() if text1 else []
    lines2 = text2.splitlines() if text2 else []
    
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    
    result = []
    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
        if opcode == 'equal':
            for i in range(i2 - i1):
                result.append({
                    'type': 'equal',
                    'left': {'line': i1 + i + 1, 'content': lines1[i1 + i]},
                    'right': {'line': j1 + i + 1, 'content': lines2[j1 + i]}
                })
        elif opcode == 'replace':
            left_lines = lines1[i1:i2]
            right_lines = lines2[j1:j2]
            max_len = max(len(left_lines), len(right_lines))
            for i in range(max_len):
                left = {'line': i1 + i + 1, 'content': left_lines[i]} if i < len(left_lines) else None
                right = {'line': j1 + i + 1, 'content': right_lines[i]} if i < len(right_lines) else None
                result.append({'type': 'change', 'left': left, 'right': right})
        elif opcode == 'delete':
            for i in range(i2 - i1):
                result.append({
                    'type': 'delete',
                    'left': {'line': i1 + i + 1, 'content': lines1[i1 + i]},
                    'right': None
                })
        elif opcode == 'insert':
            for i in range(j2 - j1):
                result.append({
                    'type': 'insert',
                    'left': None,
                    'right': {'line': j1 + i + 1, 'content': lines2[j1 + i]}
                })
    
    return result


def compare_documents(file_path1, file_path2, file_type):
    """Compare two documents and return diff information."""
    text1 = extract_text_content(file_path1, file_type)
    text2 = extract_text_content(file_path2, file_type)
    
    if text1 is None or text2 is None:
        return {
            'error': 'Cannot extract text from one or both files',
            'can_compare': False
        }
    
    return {
        'can_compare': True,
        'text_diff': text_diff(text1, text2),
        'side_by_side': side_by_side_diff(text1, text2),
        'html_diff': html_diff(text1, text2),
        'stats': get_diff_stats(text1, text2)
    }


def get_diff_stats(text1, text2):
    """Calculate statistics about the differences."""
    lines1 = text1.splitlines() if text1 else []
    lines2 = text2.splitlines() if text2 else []
    
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    
    added = 0
    removed = 0
    changed = 0
    
    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
        if opcode == 'insert':
            added += j2 - j1
        elif opcode == 'delete':
            removed += i2 - i1
        elif opcode == 'replace':
            changed += max(i2 - i1, j2 - j1)
    
    similarity = matcher.ratio() * 100
    
    return {
        'lines_added': added,
        'lines_removed': removed,
        'lines_changed': changed,
        'similarity_percent': round(similarity, 1),
        'total_lines_v1': len(lines1),
        'total_lines_v2': len(lines2)
    }
