"""
Comprehensive Codebase Review Script
Checks for errors, consistency issues, and integration problems
"""

from __future__ import annotations

import ast
import importlib.util
import os
import sys
from pathlib import Path
from typing import Dict, List, Set

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_imports(file_path: Path) -> List[str]:
    """Check for import errors in a file."""
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST
        tree = ast.parse(content, filename=str(file_path))
        
        # Check imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    try:
                        __import__(alias.name)
                    except ImportError:
                        # Check if it's an optional dependency
                        if alias.name not in ['torch', 'can', 'usb.core', 'cv2']:
                            errors.append(f"Import error: {alias.name} in {file_path}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    try:
                        __import__(node.module)
                    except ImportError:
                        # Check if it's an optional dependency
                        if node.module not in ['torch', 'can', 'usb.core', 'cv2']:
                            errors.append(f"Import error: {node.module} in {file_path}")
    except SyntaxError as e:
        errors.append(f"Syntax error in {file_path}: {e}")
    except Exception as e:
        errors.append(f"Error checking {file_path}: {e}")
    
    return errors


def check_undefined_variables(file_path: Path) -> List[str]:
    """Check for potentially undefined variables."""
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        tree = ast.parse(content, filename=str(file_path))
        
        # Simple check for common undefined patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if node.id in ['Path', 'Dict', 'List', 'Optional', 'Tuple']:
                    # Check if it's imported
                    has_import = False
                    for parent in ast.walk(tree):
                        if isinstance(parent, (ast.Import, ast.ImportFrom)):
                            if isinstance(parent, ast.ImportFrom) and parent.module == 'pathlib' and node.id == 'Path':
                                has_import = True
                            elif isinstance(parent, ast.ImportFrom) and parent.module == 'typing' and node.id in ['Dict', 'List', 'Optional', 'Tuple']:
                                has_import = True
                    if not has_import and node.id == 'Path':
                        # Check if it's used in a context that suggests it should be imported
                        if isinstance(node.ctx, ast.Load):
                            errors.append(f"Potentially undefined: {node.id} in {file_path}")
    except Exception as e:
        pass  # Ignore parsing errors, they're handled elsewhere
    
    return errors


def find_all_python_files(directory: Path) -> List[Path]:
    """Find all Python files in directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip common directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'venv', '.venv']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files


def check_service_initialization() -> List[str]:
    """Check that services are properly initialized."""
    errors = []
    
    # Check main_container.py for service initialization
    main_container = project_root / "ui" / "main_container.py"
    if main_container.exists():
        with open(main_container, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check for critical services
            required_services = [
                'backup_manager',
                'config_monitor',
                'ai_advisor',
            ]
            
            for service in required_services:
                if f'self.{service}' in content:
                    # Check if it's initialized
                    if f'self.{service} = None' in content:
                        # Check if there's initialization logic
                        if f'from services' in content or f'import' in content:
                            pass  # Likely initialized
                        else:
                            errors.append(f"Service {service} may not be properly initialized in main_container.py")
    
    return errors


def main():
    """Run comprehensive review."""
    print("=" * 60)
    print("Comprehensive Codebase Review")
    print("=" * 60)
    
    all_errors = []
    all_warnings = []
    
    # Find all Python files
    print("\n[1] Scanning Python files...")
    python_files = find_all_python_files(project_root)
    print(f"Found {len(python_files)} Python files")
    
    # Check imports
    print("\n[2] Checking imports...")
    import_errors = 0
    for file_path in python_files:
        errors = check_imports(file_path)
        if errors:
            import_errors += len(errors)
            all_errors.extend(errors)
            for error in errors:
                print(f"  ERROR: {error}")
    
    print(f"Found {import_errors} import errors")
    
    # Check undefined variables
    print("\n[3] Checking for undefined variables...")
    undefined_errors = 0
    for file_path in python_files:
        errors = check_undefined_variables(file_path)
        if errors:
            undefined_errors += len(errors)
            all_warnings.extend(errors)
            for error in errors:
                print(f"  WARNING: {error}")
    
    print(f"Found {undefined_errors} potential undefined variable issues")
    
    # Check service initialization
    print("\n[4] Checking service initialization...")
    init_errors = check_service_initialization()
    if init_errors:
        all_warnings.extend(init_errors)
        for error in init_errors:
            print(f"  WARNING: {error}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Review Summary")
    print("=" * 60)
    print(f"Total Errors: {len(all_errors)}")
    print(f"Total Warnings: {len(all_warnings)}")
    
    if all_errors:
        print("\nErrors found:")
        for error in all_errors[:10]:  # Show first 10
            print(f"  - {error}")
        if len(all_errors) > 10:
            print(f"  ... and {len(all_errors) - 10} more")
    
    if all_warnings:
        print("\nWarnings found:")
        for warning in all_warnings[:10]:  # Show first 10
            print(f"  - {warning}")
        if len(all_warnings) > 10:
            print(f"  ... and {len(all_warnings) - 10} more")
    
    if not all_errors and not all_warnings:
        print("\n✓ No critical issues found!")
    
    return len(all_errors) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
















