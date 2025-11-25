"""
UI Consistency Checker
Validates that all UI elements follow consistent styling patterns across the entire application.
"""

import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict

# Define expected theme colors (light theme)
EXPECTED_COLORS = {
    'background_primary': '#e8e9ea',
    'background_secondary': '#ffffff',
    'background_tertiary': '#ecf0f1',
    'text_primary': '#2c3e50',
    'text_secondary': '#34495e',
    'text_muted': '#5f6c7b',
    'border': '#bdc3c7',
    'border_focus': '#3498db',
    'primary': '#3498db',
    'primary_hover': '#2980b9',
    'primary_pressed': '#21618c',
}

# Colors that should NOT be used (dark theme leftovers)
FORBIDDEN_COLORS = {
    '#1a1a1a', '#2a2a2a', '#0a0a0a', '#404040', '#ffffff',  # Dark theme colors (white text is OK in some contexts)
    '#000000', '#111111', '#222222', '#333333',  # Pure black/dark grays
}

# Expected border styles
EXPECTED_BORDER_STYLES = {
    'standard': '1px solid #bdc3c7',
    'focus': '2px solid #3498db',
    'groupbox': '2px solid #bdc3c7',
}

# Expected border radius
EXPECTED_BORDER_RADIUS = {
    'button': '6px',
    'widget': '4px',
    'groupbox': '8px',
}

# Expected font sizes (scaled)
EXPECTED_FONT_SIZES = {
    'title': (18, 26),
    'subtitle': (12, 16),
    'body': (11, 14),
    'small': (9, 12),
}

# Expected spacing
EXPECTED_SPACING = {
    'layout_margin': (8, 18),
    'layout_spacing': (6, 12),
    'widget_padding': (5, 12),
}


@dataclass
class UIConsistencyIssue:
    """Represents a UI consistency issue found."""
    file: str
    line: int
    severity: str  # 'error', 'warning', 'info'
    category: str  # 'color', 'border', 'spacing', 'font', 'theme'
    message: str
    suggestion: str = ""


@dataclass
class UIConsistencyReport:
    """Complete consistency report."""
    issues: List[UIConsistencyIssue] = field(default_factory=list)
    file_stats: Dict[str, int] = field(default_factory=dict)
    summary: Dict[str, int] = field(default_factory=lambda: {
        'errors': 0,
        'warnings': 0,
        'info': 0,
        'total_files': 0,
        'files_with_issues': 0,
    })


class UIConsistencyChecker:
    """Checks UI consistency across all Python files."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.ui_dir = root_dir / "ui"
        self.report = UIConsistencyReport()
        self.color_patterns = {
            'hex_color': re.compile(r'#([0-9a-fA-F]{3,6})\b'),
            'rgb_color': re.compile(r'rgb\([^)]+\)'),
            'rgba_color': re.compile(r'rgba\([^)]+\)'),
        }
        
    def check_all(self) -> UIConsistencyReport:
        """Run all consistency checks."""
        print("[*] Starting UI Consistency Check...")
        print(f"[*] Scanning directory: {self.ui_dir}")
        
        # Find all Python files in ui directory
        ui_files = list(self.ui_dir.glob("*.py"))
        self.report.summary['total_files'] = len(ui_files)
        
        print(f"[*] Found {len(ui_files)} UI files to check\n")
        
        for ui_file in ui_files:
            if ui_file.name.startswith('__'):
                continue
            self._check_file(ui_file)
        
        # Generate summary
        self._generate_summary()
        
        return self.report
    
    def _check_file(self, file_path: Path) -> None:
        """Check a single file for consistency issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            print(f"⚠️  Error reading {file_path}: {e}")
            return
        
        file_issues = 0
        relative_path = str(file_path.relative_to(self.root_dir))
        
        # Check for various consistency issues
        file_issues += self._check_colors(content, lines, relative_path)
        file_issues += self._check_borders(content, lines, relative_path)
        file_issues += self._check_fonts(content, lines, relative_path)
        file_issues += self._check_spacing(content, lines, relative_path)
        file_issues += self._check_theme_mixing(content, lines, relative_path)
        file_issues += self._check_widget_sizing(content, lines, relative_path)
        file_issues += self._check_tab_styling(content, lines, relative_path)
        
        self.report.file_stats[relative_path] = file_issues
        
        if file_issues > 0:
            self.report.summary['files_with_issues'] += 1
    
    def _check_colors(self, content: str, lines: List[str], file_path: str) -> int:
        """Check for color consistency issues."""
        issues = 0
        
        # Find all hex colors
        for match in self.color_patterns['hex_color'].finditer(content):
            color = match.group(0).upper()
            line_num = content[:match.start()].count('\n') + 1
            
            # Check for forbidden colors
            if color in FORBIDDEN_COLORS:
                self.report.issues.append(UIConsistencyIssue(
                    file=file_path,
                    line=line_num,
                    severity='error',
                    category='color',
                    message=f"Forbidden dark theme color found: {color}",
                    suggestion=f"Replace with light theme color (e.g., {EXPECTED_COLORS.get('text_primary', '#2c3e50')} for text, {EXPECTED_COLORS.get('background_secondary', '#ffffff')} for background)"
                ))
                issues += 1
            
            # Check for inconsistent white text (should be dark on light background)
            if color == '#FFFFFF' or color == '#FFF':
                # Check context - white text might be OK in some cases (buttons, selected tabs)
                context_line = lines[line_num - 1] if line_num <= len(lines) else ""
                if 'color:' in context_line.lower() and 'background' not in context_line.lower():
                    # Might be text color on light background
                    self.report.issues.append(UIConsistencyIssue(
                        file=file_path,
                        line=line_num,
                        severity='warning',
                        category='color',
                        message=f"White text color found: {color}",
                        suggestion="Consider using dark text (#2c3e50) for better visibility on light backgrounds"
                    ))
                    issues += 1
        
        return issues
    
    def _check_borders(self, content: str, lines: List[str], file_path: str) -> int:
        """Check for border consistency issues."""
        issues = 0
        
        # Find border declarations
        border_pattern = re.compile(r'border:\s*([^;]+);', re.IGNORECASE)
        for match in border_pattern.finditer(content):
            border_value = match.group(1).strip()
            line_num = content[:match.start()].count('\n') + 1
            
            # Check for dark theme borders
            if '#404040' in border_value or '#1a1a1a' in border_value:
                self.report.issues.append(UIConsistencyIssue(
                    file=file_path,
                    line=line_num,
                    severity='error',
                    category='border',
                    message=f"Dark theme border found: {border_value}",
                    suggestion=f"Replace with light theme border: {EXPECTED_BORDER_STYLES['standard']}"
                ))
                issues += 1
            
            # Check for missing border-radius
            context_start = max(0, match.start() - 200)
            context_end = min(len(content), match.end() + 200)
            context = content[context_start:context_end]
            
            if 'border:' in context and 'border-radius:' not in context:
                # Check if it's a widget that should have rounded corners
                if any(widget in context for widget in ['QPushButton', 'QWidget', 'QGroupBox', 'QTabWidget']):
                    self.report.issues.append(UIConsistencyIssue(
                        file=file_path,
                        line=line_num,
                        severity='info',
                        category='border',
                        message=f"Border found without border-radius",
                        suggestion="Consider adding border-radius for modern appearance (4px for widgets, 6px for buttons)"
                    ))
                    issues += 1
        
        return issues
    
    def _check_fonts(self, content: str, lines: List[str], file_path: str) -> int:
        """Check for font size consistency."""
        issues = 0
        
        # Find font-size declarations
        font_pattern = re.compile(r'font-size:\s*(\d+)px', re.IGNORECASE)
        for match in font_pattern.finditer(content):
            font_size = int(match.group(1))
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if font size is within expected ranges
            context_start = max(0, match.start() - 100)
            context = content[context_start:match.start()]
            
            if 'title' in context.lower() or 'heading' in context.lower():
                if not (EXPECTED_FONT_SIZES['title'][0] <= font_size <= EXPECTED_FONT_SIZES['title'][1]):
                    self.report.issues.append(UIConsistencyIssue(
                        file=file_path,
                        line=line_num,
                        severity='warning',
                        category='font',
                        message=f"Title font size {font_size}px may be inconsistent",
                        suggestion=f"Expected title font size: {EXPECTED_FONT_SIZES['title'][0]}-{EXPECTED_FONT_SIZES['title'][1]}px"
                    ))
                    issues += 1
        
        return issues
    
    def _check_spacing(self, content: str, lines: List[str], file_path: str) -> int:
        """Check for spacing consistency."""
        issues = 0
        
        # Check for inconsistent margins
        margin_pattern = re.compile(r'setContentsMargins\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)')
        for match in margin_pattern.finditer(content):
            margins = tuple(map(int, match.groups()))
            line_num = content[:match.start()].count('\n') + 1
            
            # Check if margins are consistent (all same or reasonable variation)
            if len(set(margins)) > 2:  # More than 2 different values
                self.report.issues.append(UIConsistencyIssue(
                    file=file_path,
                    line=line_num,
                    severity='info',
                    category='spacing',
                    message=f"Inconsistent margins: {margins}",
                    suggestion="Consider using consistent margins (e.g., all 10px or 12px) for better visual consistency"
                ))
                issues += 1
        
        return issues
    
    def _check_theme_mixing(self, content: str, lines: List[str], file_path: str) -> int:
        """Check for mixing of light and dark theme elements."""
        issues = 0
        
        # Check for dark backgrounds with light text (should be consistent)
        dark_bg_pattern = re.compile(r'background.*#(?:1a|2a|0a|00)[0-9a-fA-F]{4}', re.IGNORECASE)
        light_text_pattern = re.compile(r'color.*#(?:fff|ffffff)', re.IGNORECASE)
        
        has_dark_bg = bool(dark_bg_pattern.search(content))
        has_light_text = bool(light_text_pattern.search(content))
        
        if has_dark_bg and not has_light_text:
            # Dark background but no light text - might be inconsistent
            for match in dark_bg_pattern.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                self.report.issues.append(UIConsistencyIssue(
                    file=file_path,
                    line=line_num,
                    severity='error',
                    category='theme',
                    message="Dark background found - should use light theme",
                    suggestion=f"Replace with light theme background: {EXPECTED_COLORS['background_secondary']}"
                ))
                issues += 1
        
        return issues
    
    def _check_widget_sizing(self, content: str, lines: List[str], file_path: str) -> int:
        """Check for widget sizing consistency."""
        issues = 0
        
        # Check for hardcoded sizes that might be inconsistent
        size_pattern = re.compile(r'set(?:Minimum|Maximum)(?:Width|Height|Size)\((\d+)\)')
        sizes_found = []
        
        for match in size_pattern.finditer(content):
            size = int(match.group(1))
            sizes_found.append(size)
        
        # Check for common inconsistent sizes
        if sizes_found:
            unique_sizes = set(sizes_found)
            if len(unique_sizes) > 10:  # Too many different sizes
                self.report.issues.append(UIConsistencyIssue(
                    file=file_path,
                    line=0,
                    severity='info',
                    category='sizing',
                    message=f"Many different widget sizes found: {len(unique_sizes)} unique sizes",
                    suggestion="Consider standardizing widget sizes for consistency"
                ))
                issues += 1
        
        return issues
    
    def _check_tab_styling(self, content: str, lines: List[str], file_path: str) -> int:
        """Check for tab widget styling consistency."""
        issues = 0
        
        # Check if QTabWidget is used
        if 'QTabWidget' in content or 'QTabBar' in content:
            # Check for consistent tab styling
            if 'QTabWidget::pane' not in content and 'setStyleSheet' in content:
                # Tabs might not have consistent styling
                self.report.issues.append(UIConsistencyIssue(
                    file=file_path,
                    line=0,
                    severity='warning',
                    category='theme',
                    message="QTabWidget found but may lack consistent styling",
                    suggestion="Ensure QTabWidget::pane and QTabBar::tab styles are defined consistently"
                ))
                issues += 1
            
            # Check for dark theme tab colors
            if '#1a1a1a' in content or '#2a2a2a' in content:
                tab_line = next((i for i, line in enumerate(lines) if 'QTab' in line and ('#1a1a1a' in line or '#2a2a2a' in line)), None)
                if tab_line:
                    self.report.issues.append(UIConsistencyIssue(
                        file=file_path,
                        line=tab_line + 1,
                        severity='error',
                        category='theme',
                        message="Dark theme colors in tab styling",
                        suggestion="Use light theme colors: background #ffffff, tabs #ecf0f1, selected #3498db"
                    ))
                    issues += 1
        
        return issues
    
    def _generate_summary(self) -> None:
        """Generate summary statistics."""
        for issue in self.report.issues:
            if issue.severity == 'error':
                self.report.summary['errors'] += 1
            elif issue.severity == 'warning':
                self.report.summary['warnings'] += 1
            else:
                self.report.summary['info'] += 1
    
    def print_report(self) -> None:
        """Print a formatted report."""
        print("\n" + "="*80)
        print("📊 UI CONSISTENCY REPORT")
        print("="*80)
        print(f"\n📁 Files Scanned: {self.report.summary['total_files']}")
        print(f"⚠️  Files with Issues: {self.report.summary['files_with_issues']}")
        print(f"\n📈 Issues Found:")
        print(f"   🔴 Errors: {self.report.summary['errors']}")
        print(f"   🟡 Warnings: {self.report.summary['warnings']}")
        print(f"   🔵 Info: {self.report.summary['info']}")
        print(f"   📊 Total: {len(self.report.issues)}")
        
        if self.report.issues:
            print("\n" + "="*80)
            print("🔍 DETAILED ISSUES")
            print("="*80)
            
            # Group by file
            issues_by_file = defaultdict(list)
            for issue in self.report.issues:
                issues_by_file[issue.file].append(issue)
            
            for file_path, file_issues in sorted(issues_by_file.items()):
                print(f"\n📄 {file_path}")
                print("-" * 80)
                
                for issue in sorted(file_issues, key=lambda x: (x.severity, x.line)):
                    severity_icon = {
                        'error': '🔴',
                        'warning': '🟡',
                        'info': '🔵'
                    }.get(issue.severity, '⚪')
                    
                    print(f"  {severity_icon} Line {issue.line:4d} [{issue.category.upper():8s}] {issue.message}")
                    if issue.suggestion:
                        print(f"      💡 Suggestion: {issue.suggestion}")
        else:
            print("\n✅ No consistency issues found! UI is consistent across all files.")
        
        print("\n" + "="*80)
    
    def export_report(self, output_file: Path) -> None:
        """Export report to a file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("UI Consistency Report\n")
            f.write("="*80 + "\n\n")
            f.write(f"Files Scanned: {self.report.summary['total_files']}\n")
            f.write(f"Files with Issues: {self.report.summary['files_with_issues']}\n")
            f.write(f"Errors: {self.report.summary['errors']}\n")
            f.write(f"Warnings: {self.report.summary['warnings']}\n")
            f.write(f"Info: {self.report.summary['info']}\n")
            f.write(f"Total Issues: {len(self.report.issues)}\n\n")
            
            if self.report.issues:
                f.write("DETAILED ISSUES\n")
                f.write("="*80 + "\n\n")
                
                for issue in sorted(self.report.issues, key=lambda x: (x.file, x.line)):
                    f.write(f"{issue.file}:{issue.line} [{issue.severity.upper()}] {issue.message}\n")
                    if issue.suggestion:
                        f.write(f"  Suggestion: {issue.suggestion}\n")
                    f.write("\n")


def main():
    """Main entry point."""
    import sys
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Run checker
    checker = UIConsistencyChecker(project_root)
    report = checker.check_all()
    
    # Print report
    checker.print_report()
    
    # Export report
    report_file = project_root / "docs" / "UI_CONSISTENCY_REPORT.md"
    report_file.parent.mkdir(exist_ok=True)
    checker.export_report(report_file)
    print(f"\n📝 Report exported to: {report_file}")
    
    # Exit with error code if there are errors
    if report.summary['errors'] > 0:
        sys.exit(1)
    elif report.summary['warnings'] > 0:
        sys.exit(0)  # Warnings are OK
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

