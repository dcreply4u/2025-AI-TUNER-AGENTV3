"""
Module Integrator for AI Tuner CAN Agent

Automatically integrates generated modules into the codebase,
updates __init__.py files, and ensures no duplicates.
"""

import os
import sys
import ast
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional
import importlib.util

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class ModuleIntegrator:
    """
    Integrates generated modules into the codebase.
    """
    
    def __init__(self, generated_dir: str, base_package: str = "ai_tuner_can_agent"):
        """
        Initialize module integrator.
        
        Args:
            generated_dir: Directory containing generated modules
            base_package: Base package name for imports
        """
        self.generated_dir = Path(generated_dir)
        self.base_package = base_package
        self.integrated_modules: List[str] = []
    
    def analyze_module(self, module_path: Path) -> Dict:
        """
        Analyze a Python module to extract its structure.
        
        Args:
            module_path: Path to module file
            
        Returns:
            Dictionary with module information
        """
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    else:
                        imports.append(node.module or '')
            
            return {
                "path": module_path,
                "name": module_path.stem,
                "classes": classes,
                "functions": functions,
                "imports": imports,
                "content": content
            }
        except Exception as e:
            logger.error(f"Error analyzing {module_path}: {e}")
            return {}
    
    def find_best_location(self, module_info: Dict) -> Optional[Path]:
        """
        Find the best location for a module based on its content.
        
        Args:
            module_info: Module information dictionary
            
        Returns:
            Best target path or None
        """
        # Determine category based on content and imports
        content_lower = module_info.get("content", "").lower()
        imports = module_info.get("imports", [])
        
        base_dir = self.generated_dir.parent
        
        # CAN/UDS related
        if any(keyword in content_lower for keyword in ['can', 'uds', 'bus', 'message', 'frame']):
            target = base_dir / "can_uds"
            target.mkdir(exist_ok=True)
            return target / f"{module_info['name']}.py"
        
        # Telemetry related
        if any(keyword in content_lower for keyword in ['telemetry', 'mqtt', 'publish', 'buffer']):
            target = base_dir / "telemetry"
            target.mkdir(exist_ok=True)
            return target / f"{module_info['name']}.py"
        
        # Analytics related
        if any(keyword in content_lower for keyword in ['analytics', 'analysis', 'statistics', 'score', 'health']):
            target = base_dir / "analytics"
            target.mkdir(exist_ok=True)
            return target / f"{module_info['name']}.py"
        
        # Config related
        if any(keyword in content_lower for keyword in ['config', 'setting', 'parameter']):
            target = base_dir / "config"
            target.mkdir(exist_ok=True)
            return target / f"{module_info['name']}.py"
        
        # Advanced features
        if any(keyword in content_lower for keyword in ['async', 'advanced', 'ml', 'ai', 'predictive']):
            target = base_dir / "advanced"
            target.mkdir(exist_ok=True)
            return target / f"{module_info['name']}.py"
        
        # Default: keep in generated or utils
        target = base_dir / "utils"
        target.mkdir(exist_ok=True)
        return target / f"{module_info['name']}.py"
    
    def check_duplicates(self, module_info: Dict, target_path: Path) -> bool:
        """
        Check if module would create duplicates.
        
        Args:
            module_info: Module information
            target_path: Target path for module
            
        Returns:
            True if duplicates found, False otherwise
        """
        if not target_path.exists():
            return False
        
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            existing_tree = ast.parse(existing_content)
            existing_classes = {node.name for node in ast.walk(existing_tree) if isinstance(node, ast.ClassDef)}
            existing_functions = {node.name for node in ast.walk(existing_tree) if isinstance(node, ast.FunctionDef)}
            
            module_classes = set(module_info.get("classes", []))
            module_functions = set(module_info.get("functions", []))
            
            # Check for duplicate class/function names
            duplicate_classes = module_classes & existing_classes
            duplicate_functions = module_functions & existing_functions
            
            if duplicate_classes:
                logger.warning(f"Duplicate classes in {target_path.name}: {duplicate_classes}")
                return True
            
            if duplicate_functions:
                logger.warning(f"Duplicate functions in {target_path.name}: {duplicate_functions}")
                return True
            
            return False
        except Exception as e:
            logger.warning(f"Could not check duplicates in {target_path}: {e}")
            return False
    
    def integrate(self, module_path: Path, target_path: Optional[Path] = None) -> bool:
        """
        Integrate a module into the codebase.
        
        Args:
            module_path: Path to module to integrate
            target_path: Optional target path (auto-determined if None)
            
        Returns:
            True if successful, False otherwise
        """
        module_info = self.analyze_module(module_path)
        if not module_info:
            return False
        
        if target_path is None:
            target_path = self.find_best_location(module_info)
        
        if target_path is None:
            logger.error(f"Could not determine target location for {module_path.name}")
            return False
        
        # Check for duplicates
        if self.check_duplicates(module_info, target_path):
            logger.warning(f"Skipping {module_path.name} due to duplicates")
            return False
        
        # Copy module to target location
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(module_info["content"], encoding='utf-8')
            
            logger.info(f"Integrated {module_path.name} -> {target_path}")
            self.integrated_modules.append(str(target_path))
            
            # Update __init__.py
            self._update_init_file(target_path.parent)
            
            return True
        except Exception as e:
            logger.error(f"Error integrating {module_path.name}: {e}")
            return False
    
    def _update_init_file(self, package_dir: Path):
        """Update __init__.py file to export new modules."""
        init_file = package_dir / "__init__.py"
        
        # Get all Python modules in directory
        modules = [f.stem for f in package_dir.glob("*.py") if f.name != "__init__.py"]
        
        if not modules:
            return
        
        # Read existing init file
        existing_content = ""
        if init_file.exists():
            existing_content = init_file.read_text(encoding='utf-8')
        
        # Generate __all__ list
        all_list = sorted(set(modules))
        
        # Create/update init file
        init_content = f'''"""
{package_dir.name.title()} package for AI Tuner CAN Agent
"""

'''
        
        # Add explicit imports (avoid wildcard imports)
        # First, try to extract __all__ from each module
        imported_items = []
        for module in all_list:
            module_path = package_dir / f"{module}.py"
            if module_path.exists():
                try:
                    with open(module_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Try to find __all__ definition
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id == '__all__':
                                    if isinstance(node.value, (ast.List, ast.Tuple)):
                                        items = [elt.s for elt in node.value.elts if isinstance(elt, ast.Constant)]
                                        for item in items:
                                            imported_items.append(f"{module}.{item}")
                                        init_content += f"from .{module} import {', '.join(items)}\n"
                                        break
                    # If no __all__ found, import common patterns
                    if not any(f"from .{module}" in line for line in init_content.split('\n')):
                        # Extract classes and functions
                        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                        exports = [name for name in classes + functions if not name.startswith('_')]
                        if exports:
                            init_content += f"from .{module} import {', '.join(exports[:10])}\n"  # Limit to 10 to avoid clutter
                            imported_items.extend([f"{module}.{item}" for item in exports[:10]])
                except Exception as e:
                    logger.warning(f"Could not parse {module}.py for imports: {e}")
                    # Fallback: import module itself
                    init_content += f"from . import {module}\n"
                    imported_items.append(module)
        
        init_content += f'''
__all__ = {sorted(set(imported_items))!r}
'''
        
        # Only update if changed
        if init_content != existing_content:
            init_file.write_text(init_content, encoding='utf-8')
            logger.info(f"Updated {init_file}")
    
    def integrate_all(self) -> int:
        """
        Integrate all modules from generated directory.
        
        Returns:
            Number of successfully integrated modules
        """
        if not self.generated_dir.exists():
            logger.warning(f"Generated directory does not exist: {self.generated_dir}")
            return 0
        
        count = 0
        for module_file in self.generated_dir.glob("*.py"):
            if module_file.name == "__init__.py":
                continue
            
            if self.integrate(module_file):
                count += 1
        
        logger.info(f"Successfully integrated {count} modules")
        return count


def main():
    """Main integration function."""
    base_dir = Path(__file__).parent
    generated_dir = base_dir / "generated_modules"
    
    integrator = ModuleIntegrator(str(generated_dir))
    count = integrator.integrate_all()
    
    return count


if __name__ == "__main__":
    try:
        count = main()
        sys.exit(0 if count > 0 else 1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)

