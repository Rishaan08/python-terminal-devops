import os
import shutil
import shlex
import psutil
import time
import hashlib
from typing import Tuple, List
from datetime import datetime

class CommandExecutor:
    """
    Execute a limited set of terminal-like commands safely using Python APIs.
    All commands accept a cwd and return (stdout, stderr, new_cwd, exit_code).
    """

    def __init__(self):
        self.heredoc_mode = None  # Store heredoc state: {'mode', 'filepath', 'delimiter', 'lines'}
        self.input_mode = None     # Store input mode state: {'mode', 'filepath', 'lines'}

    def run(self, raw_cmd: str, cwd: str = None) -> Tuple[str, str, str, int]:
        if cwd is None:
            cwd = "/tmp"
            os.makedirs(cwd, exist_ok=True)

        raw_cmd = raw_cmd.strip()
        
        # Handle heredoc mode continuation
        if self.heredoc_mode:
            if raw_cmd == self.heredoc_mode['delimiter']:
                # End of heredoc, write to file
                filepath = self.heredoc_mode['filepath']
                mode = self.heredoc_mode['mode']
                content = "\n".join(self.heredoc_mode['lines'])
                try:
                    with open(filepath, mode, encoding="utf-8") as f:
                        f.write(content + "\n")
                    self.heredoc_mode = None
                    return ("", "", cwd, 0)
                except Exception as e:
                    self.heredoc_mode = None
                    return ("", f"cat: write error: {e}\n", cwd, 1)
            else:
                # Accumulate lines
                self.heredoc_mode['lines'].append(raw_cmd)
                return ("> ", "", cwd, 0)
        
        # Handle input mode continuation  
        if self.input_mode:
            if raw_cmd == "":  # Ctrl+D simulation (empty line ends input)
                # End of input, write to file
                filepath = self.input_mode['filepath']
                mode = self.input_mode['mode']
                content = "\n".join(self.input_mode['lines'])
                try:
                    with open(filepath, mode, encoding="utf-8") as f:
                        f.write(content + "\n")
                    self.input_mode = None
                    return ("", "", cwd, 0)
                except Exception as e:
                    self.input_mode = None
                    return ("", f"cat: write error: {e}\n", cwd, 1)
            else:
                # Accumulate lines
                self.input_mode['lines'].append(raw_cmd)
                return ("> ", "", cwd, 0)
        
        if not raw_cmd:
            return ("", "", cwd, 0)

        # simple split while respecting quotes
        try:
            parts = shlex.split(raw_cmd)
        except ValueError as e:
            return ("", f"parse error: {e}", cwd, 2)

        cmd = parts[0]
        args = parts[1:]

        try:
            if cmd == "pwd":
                return (cwd + "\n", "", cwd, 0)

            if cmd == "ls":
                return self._ls(args, cwd)

            if cmd == "cd":
                return self._cd(args, cwd)

            if cmd == "mkdir":
                return self._mkdir(args, cwd)

            if cmd == "rm":
                return self._rm(args, cwd)

            if cmd == "rmdir":
                return self._rmdir(args, cwd)

            if cmd == "cat":
                result = self._cat(args, cwd)
                # Check for special modes
                if result[0].startswith("HEREDOC_MODE:"):
                    parts = result[0].split(":", 3)
                    self.heredoc_mode = {
                        'mode': parts[1],
                        'filepath': parts[2],
                        'delimiter': parts[3],
                        'lines': []
                    }
                    return ("> ", "", cwd, 0)
                elif result[0].startswith("INPUT_MODE:"):
                    parts = result[0].split(":", 2)
                    self.input_mode = {
                        'mode': parts[1],
                        'filepath': parts[2],
                        'lines': []
                    }
                    return ("> ", "", cwd, 0)
                return result

            if cmd == "touch":
                return self._touch(args, cwd)

            if cmd == "mv":
                return self._mv(args, cwd)

            if cmd == "cp":
                return self._cp(args, cwd)

            if cmd == "echo":
                return self._echo(args, cwd)

            if cmd == "cpu":
                return self._cpu()

            if cmd == "mem":
                return self._mem()

            if cmd == "ps":
                return self._ps(args)

            # New commands
            if cmd == "head":
                return self._head(args, cwd)

            if cmd == "tail":
                return self._tail(args, cwd)

            if cmd == "wc":
                return self._wc(args, cwd)

            if cmd == "grep":
                return self._grep(args, cwd)

            if cmd == "find":
                return self._find(args, cwd)

            if cmd == "tree":
                return self._tree(args, cwd)

            if cmd == "du":
                return self._du(args, cwd)

            if cmd == "df":
                return self._df(args, cwd)

            if cmd == "stat":
                return self._stat(args, cwd)

            if cmd == "chmod":
                return self._chmod(args, cwd)

            if cmd == "date":
                return self._date(args, cwd)

            if cmd == "uptime":
                return self._uptime()

            if cmd == "whoami":
                return self._whoami(cwd)

            if cmd == "hostname":
                return self._hostname(cwd)

            if cmd == "md5sum":
                return self._md5sum(args, cwd)

            if cmd == "sha256sum":
                return self._sha256sum(args, cwd)

            if cmd == "clear":
                return self._clear(cwd)

            if cmd == "which":
                return self._which(args, cwd)

            # help
            if cmd in ("help", "--help", "-h"):
                return (self._help_text(), "", cwd, 0)

            return ("", f"Command not found: {cmd}\n", cwd, 127)
        except Exception as e:
            return ("", f"Error: {e}\n", cwd, 1)

    # --- Implementations ---

    def _path_resolve(self, path: str, cwd: str) -> str:
        if os.path.isabs(path):
            return os.path.normpath(path)
        return os.path.normpath(os.path.join(cwd, path))

    def _ls(self, args: List[str], cwd: str):
        target = cwd
        long_format = False
        show_all = False
        
        i = 0
        while i < len(args):
            if args[i] == "-l":
                long_format = True
            elif args[i] == "-a":
                show_all = True
            elif args[i] == "-la" or args[i] == "-al":
                long_format = True
                show_all = True
            elif not args[i].startswith("-"):
                target = self._path_resolve(args[i], cwd)
            i += 1

        if not os.path.exists(target):
            return ("", f"ls: cannot access '{target}': No such file or directory\n", cwd, 2)

        if os.path.isfile(target):
            return (os.path.basename(target) + "\n", "", cwd, 0)

        entries = os.listdir(target)
        if not show_all:
            entries = [e for e in entries if not e.startswith('.')]
        entries = sorted(entries)
        
        if long_format:
            lines = []
            for e in entries:
                p = os.path.join(target, e)
                try:
                    size = os.path.getsize(p)
                    mtime = datetime.fromtimestamp(os.path.getmtime(p)).strftime('%Y-%m-%d %H:%M')
                    dtype = "d" if os.path.isdir(p) else "-"
                    lines.append(f"{dtype}  {size:10d}  {mtime}  {e}")
                except:
                    lines.append(f"?  {'?':>10}  {'?':>16}  {e}")
            return ("\n".join(lines) + ("\n" if lines else ""), "", cwd, 0)
        else:
            return ("  ".join(entries) + ("\n" if entries else "\n"), "", cwd, 0)

    def _cd(self, args: List[str], cwd: str):
        if not args:
            new = os.path.expanduser("~")
        else:
            new = self._path_resolve(args[0], cwd)

        if not os.path.exists(new):
            return ("", f"cd: {args[0]}: No such file or directory\n", cwd, 1)
        if not os.path.isdir(new):
            return ("", f"cd: {args[0]}: Not a directory\n", cwd, 1)
        return ("", "", new, 0)

    def _mkdir(self, args: List[str], cwd: str):
        if not args:
            return ("", "mkdir: missing operand\n", cwd, 2)
        for a in args:
            p = self._path_resolve(a, cwd)
            try:
                os.makedirs(p, exist_ok=False)
            except FileExistsError:
                return ("", f"mkdir: cannot create directory '{a}': File exists\n", cwd, 1)
        return ("", "", cwd, 0)

    def _rm(self, args: List[str], cwd: str):
        if not args:
            return ("", "rm: missing operand\n", cwd, 2)

        recursive = False
        paths = []
        for a in args:
            if a in ("-r", "-rf", "-fr"):
                recursive = True
            else:
                paths.append(a)

        if not paths:
            return ("", "rm: missing path\n", cwd, 2)

        for p in paths:
            rp = self._path_resolve(p, cwd)
            if not os.path.exists(rp):
                return ("", f"rm: cannot remove '{p}': No such file or directory\n", cwd, 1)
            if os.path.isdir(rp) and not recursive:
                return ("", f"rm: cannot remove '{p}': Is a directory\n", cwd, 1)
            if os.path.isdir(rp):
                shutil.rmtree(rp)
            else:
                os.remove(rp)
        return ("", "", cwd, 0)

    def _rmdir(self, args: List[str], cwd: str):
        if not args:
            return ("", "rmdir: missing operand\n", cwd, 2)
        for a in args:
            path = self._path_resolve(a, cwd)
            if not os.path.exists(path):
                return ("", f"rmdir: failed to remove '{a}': No such file or directory\n", cwd, 1)
            if not os.path.isdir(path):
                return ("", f"rmdir: failed to remove '{a}': Not a directory\n", cwd, 1)
            try:
                os.rmdir(path)  # only removes empty directories
            except OSError:
                return ("", f"rmdir: failed to remove '{a}': Directory not empty\n", cwd, 1)
        return ("", "", cwd, 0)

    def _echo(self, args: List[str], cwd: str):
        # handle redirection operators
        if ">" in args:
            try:
                idx = args.index(">")
                text = " ".join(args[:idx])
                filepath = self._path_resolve(args[idx + 1], cwd)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(text + "\n")
                return ("", "", cwd, 0)
            except Exception as e:
                return ("", f"echo: redirection error: {e}\n", cwd, 1)

        if ">>" in args:
            try:
                idx = args.index(">>")
                text = " ".join(args[:idx])
                filepath = self._path_resolve(args[idx + 1], cwd)
                with open(filepath, "a", encoding="utf-8") as f:
                    f.write(text + "\n")
                return ("", "", cwd, 0)
            except Exception as e:
                return ("", f"echo: redirection error: {e}\n", cwd, 1)

        # default: just print text
        return (" ".join(args) + "\n", "", cwd, 0)

    def _cat(self, args: List[str], cwd: str):
        # Handle heredoc-style input: cat >> file << EOF or cat > file << EOF
        if "<<" in args:
            try:
                redirect_idx = -1
                heredoc_idx = args.index("<<")
                mode = "a"  # default append
                
                # Check for > or >> before <<
                if ">>" in args:
                    redirect_idx = args.index(">>")
                    mode = "a"
                elif ">" in args:
                    redirect_idx = args.index(">")
                    mode = "w"
                
                if redirect_idx == -1 or heredoc_idx < redirect_idx:
                    return ("", "cat: invalid syntax, use: cat [>>|>] file << EOF\n", cwd, 2)
                
                filepath = self._path_resolve(args[redirect_idx + 1], cwd)
                delimiter = args[heredoc_idx + 1] if heredoc_idx + 1 < len(args) else "EOF"
                
                # Return special signal for heredoc mode
                return (f"HEREDOC_MODE:{mode}:{filepath}:{delimiter}", "", cwd, 0)
            except Exception as e:
                return ("", f"cat: heredoc error: {e}\n", cwd, 1)
        
        # Handle regular append: cat >> file
        if ">>" in args:
            try:
                idx = args.index(">>")
                if idx == 0:
                    # No files to read, just open for input
                    filepath = self._path_resolve(args[idx + 1], cwd)
                    return (f"INPUT_MODE:a:{filepath}", "", cwd, 0)
                else:
                    # Read files and append to target
                    files_to_read = args[:idx]
                    filepath = self._path_resolve(args[idx + 1], cwd)
                    content_parts = []
                    for a in files_to_read:
                        p = self._path_resolve(a, cwd)
                        if not os.path.exists(p):
                            return ("", f"cat: {a}: No such file or directory\n", cwd, 1)
                        if os.path.isdir(p):
                            return ("", f"cat: {a}: Is a directory\n", cwd, 1)
                        with open(p, "r", encoding="utf-8", errors="replace") as f:
                            content_parts.append(f.read())
                    
                    with open(filepath, "a", encoding="utf-8") as f:
                        f.write("\n".join(content_parts))
                    return ("", "", cwd, 0)
            except Exception as e:
                return ("", f"cat: append error: {e}\n", cwd, 1)
        
        # Handle regular write: cat > file
        if ">" in args:
            try:
                idx = args.index(">")
                if idx == 0:
                    # No files to read, just open for input
                    filepath = self._path_resolve(args[idx + 1], cwd)
                    return (f"INPUT_MODE:w:{filepath}", "", cwd, 0)
                else:
                    # Read files and write to target
                    files_to_read = args[:idx]
                    filepath = self._path_resolve(args[idx + 1], cwd)
                    content_parts = []
                    for a in files_to_read:
                        p = self._path_resolve(a, cwd)
                        if not os.path.exists(p):
                            return ("", f"cat: {a}: No such file or directory\n", cwd, 1)
                        if os.path.isdir(p):
                            return ("", f"cat: {a}: Is a directory\n", cwd, 1)
                        with open(p, "r", encoding="utf-8", errors="replace") as f:
                            content_parts.append(f.read())
                    
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write("\n".join(content_parts))
                    return ("", "", cwd, 0)
            except Exception as e:
                return ("", f"cat: write error: {e}\n", cwd, 1)
        
        # Regular cat: display file contents
        if not args:
            return ("", "cat: missing file operand\n", cwd, 2)
        out_lines = []
        for a in args:
            p = self._path_resolve(a, cwd)
            if not os.path.exists(p):
                return ("", f"cat: {a}: No such file or directory\n", cwd, 1)
            if os.path.isdir(p):
                return ("", f"cat: {a}: Is a directory\n", cwd, 1)
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                out_lines.append(f.read())
        return ("\n".join(out_lines), "", cwd, 0)

    def _touch(self, args: List[str], cwd: str):
        if not args:
            return ("", "touch: missing file operand\n", cwd, 2)
        for a in args:
            p = self._path_resolve(a, cwd)
            dirp = os.path.dirname(p)
            if dirp and not os.path.exists(dirp):
                os.makedirs(dirp, exist_ok=True)
            with open(p, "a"):
                os.utime(p, None)
        return ("", "", cwd, 0)

    def _mv(self, args: List[str], cwd: str):
        if len(args) < 2:
            return ("", "mv: missing file operands\n", cwd, 2)
        srcs = [self._path_resolve(a, cwd) for a in args[:-1]]
        dest = self._path_resolve(args[-1], cwd)
        if len(srcs) > 1 and not os.path.isdir(dest):
            return ("", "mv: target is not a directory\n", cwd, 1)
        try:
            for s in srcs:
                if not os.path.exists(s):
                    return ("", f"mv: cannot stat '{s}': No such file or directory\n", cwd, 1)
                if os.path.isdir(dest):
                    shutil.move(s, os.path.join(dest, os.path.basename(s)))
                else:
                    shutil.move(s, dest)
            return ("", "", cwd, 0)
        except Exception as e:
            return ("", f"mv error: {e}\n", cwd, 1)

    def _cp(self, args: List[str], cwd: str):
        if len(args) < 2:
            return ("", "cp: missing file operands\n", cwd, 2)
        recursive = False
        files = []
        dest = None
        for a in args:
            if a == "-r":
                recursive = True
            else:
                files.append(a)
        if len(files) < 2:
            return ("", "cp: missing destination file operand after source\n", cwd, 2)
        srcs = [self._path_resolve(a, cwd) for a in files[:-1]]
        dest = self._path_resolve(files[-1], cwd)
        if len(srcs) > 1 and not os.path.isdir(dest):
            return ("", "cp: target is not a directory\n", cwd, 1)
        try:
            for s in srcs:
                if not os.path.exists(s):
                    return ("", f"cp: cannot stat '{s}': No such file or directory\n", cwd, 1)
                if os.path.isdir(s):
                    if not recursive:
                        return ("", f"cp: -r not specified; omitting directory '{s}'\n", cwd, 1)
                    target = dest if os.path.isdir(dest) else dest
                    shutil.copytree(s, os.path.join(target, os.path.basename(s)))
                else:
                    if os.path.isdir(dest):
                        shutil.copy2(s, os.path.join(dest, os.path.basename(s)))
                    else:
                        shutil.copy2(s, dest)
            return ("", "", cwd, 0)
        except Exception as e:
            return ("", f"cp error: {e}\n", cwd, 1)

    def _cpu(self):
        perc = psutil.cpu_percent(interval=0.5, percpu=False)
        return (f"CPU: {perc}%\n", "", None, 0)

    def _mem(self):
        m = psutil.virtual_memory()
        total = m.total
        used = m.used
        percent = m.percent
        return (f"Memory: {used}/{total} bytes ({percent}%)\n", "", None, 0)

    def _ps(self, args: List[str]):
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            info = p.info
            procs.append(f"{info.get('pid'):6d} {info.get('name')[:20]:20s} CPU%:{info.get('cpu_percent'):5.1f} MEM%:{info.get('memory_percent'):5.1f}")
        procs_sorted = sorted(procs)[:200]  # limit
        return ("\n".join(procs_sorted) + "\n", "", None, 0)

    # --- New Commands ---

    def _head(self, args: List[str], cwd: str):
        """Display first n lines of a file (default 10)"""
        lines = 10
        filepath = None
        
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                try:
                    lines = int(args[i + 1])
                    i += 2
                    continue
                except ValueError:
                    return ("", "head: invalid number of lines\n", cwd, 1)
            else:
                filepath = args[i]
                i += 1
        
        if not filepath:
            return ("", "head: missing file operand\n", cwd, 2)
        
        p = self._path_resolve(filepath, cwd)
        if not os.path.exists(p):
            return ("", f"head: {filepath}: No such file or directory\n", cwd, 1)
        if os.path.isdir(p):
            return ("", f"head: {filepath}: Is a directory\n", cwd, 1)
        
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            result = "".join([f.readline() for _ in range(lines)])
        return (result, "", cwd, 0)

    def _tail(self, args: List[str], cwd: str):
        """Display last n lines of a file (default 10)"""
        lines = 10
        filepath = None
        
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                try:
                    lines = int(args[i + 1])
                    i += 2
                    continue
                except ValueError:
                    return ("", "tail: invalid number of lines\n", cwd, 1)
            else:
                filepath = args[i]
                i += 1
        
        if not filepath:
            return ("", "tail: missing file operand\n", cwd, 2)
        
        p = self._path_resolve(filepath, cwd)
        if not os.path.exists(p):
            return ("", f"tail: {filepath}: No such file or directory\n", cwd, 1)
        if os.path.isdir(p):
            return ("", f"tail: {filepath}: Is a directory\n", cwd, 1)
        
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
            result = "".join(all_lines[-lines:])
        return (result, "", cwd, 0)

    def _wc(self, args: List[str], cwd: str):
        """Count lines, words, and characters in a file"""
        if not args:
            return ("", "wc: missing file operand\n", cwd, 2)
        
        results = []
        for filepath in args:
            p = self._path_resolve(filepath, cwd)
            if not os.path.exists(p):
                return ("", f"wc: {filepath}: No such file or directory\n", cwd, 1)
            if os.path.isdir(p):
                return ("", f"wc: {filepath}: Is a directory\n", cwd, 1)
            
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                lines = content.count('\n')
                words = len(content.split())
                chars = len(content)
                results.append(f"{lines:7d} {words:7d} {chars:7d} {filepath}")
        
        return ("\n".join(results) + "\n", "", cwd, 0)

    def _grep(self, args: List[str], cwd: str):
        """Search for pattern in files"""
        if len(args) < 2:
            return ("", "grep: missing pattern or file\n", cwd, 2)
        
        pattern = args[0]
        filepath = args[1]
        
        p = self._path_resolve(filepath, cwd)
        if not os.path.exists(p):
            return ("", f"grep: {filepath}: No such file or directory\n", cwd, 1)
        if os.path.isdir(p):
            return ("", f"grep: {filepath}: Is a directory\n", cwd, 1)
        
        matches = []
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for line_num, line in enumerate(f, 1):
                if pattern in line:
                    matches.append(f"{line_num}:{line.rstrip()}")
        
        if matches:
            return ("\n".join(matches) + "\n", "", cwd, 0)
        else:
            return ("", "", cwd, 1)

    def _find(self, args: List[str], cwd: str):
        """Find files matching a name pattern"""
        start_path = cwd
        name_pattern = None
        
        i = 0
        while i < len(args):
            if args[i] == "-name" and i + 1 < len(args):
                name_pattern = args[i + 1]
                i += 2
            elif not args[i].startswith("-"):
                start_path = self._path_resolve(args[i], cwd)
                i += 1
            else:
                i += 1
        
        if not os.path.exists(start_path):
            return ("", f"find: '{start_path}': No such file or directory\n", cwd, 1)
        
        results = []
        for root, dirs, files in os.walk(start_path):
            for name in files + dirs:
                if name_pattern is None or name_pattern in name:
                    results.append(os.path.join(root, name))
        
        return ("\n".join(results) + ("\n" if results else ""), "", cwd, 0)

    def _tree(self, args: List[str], cwd: str):
        """Display directory tree structure"""
        start_path = cwd
        if args:
            start_path = self._path_resolve(args[0], cwd)
        
        if not os.path.exists(start_path):
            return ("", f"tree: {args[0]}: No such file or directory\n", cwd, 1)
        
        def build_tree(path, prefix=""):
            lines = []
            try:
                entries = sorted(os.listdir(path))
            except PermissionError:
                return [f"{prefix}[Permission Denied]"]
            
            for i, entry in enumerate(entries):
                full_path = os.path.join(path, entry)
                is_last = i == len(entries) - 1
                current_prefix = "└── " if is_last else "├── "
                lines.append(f"{prefix}{current_prefix}{entry}")
                
                if os.path.isdir(full_path) and not os.path.islink(full_path):
                    extension = "    " if is_last else "│   "
                    lines.extend(build_tree(full_path, prefix + extension))
            
            return lines
        
        output = [start_path] + build_tree(start_path)
        return ("\n".join(output) + "\n", "", cwd, 0)

    def _du(self, args: List[str], cwd: str):
        """Display disk usage"""
        target = cwd
        if args:
            target = self._path_resolve(args[0], cwd)
        
        if not os.path.exists(target):
            return ("", f"du: {args[0]}: No such file or directory\n", cwd, 1)
        
        if os.path.isfile(target):
            size = os.path.getsize(target)
            return (f"{size}\t{target}\n", "", cwd, 0)
        
        total = 0
        for root, dirs, files in os.walk(target):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                except:
                    pass
        
        return (f"{total}\t{target}\n", "", cwd, 0)

    def _df(self, args: List[str], cwd: str):
        """Display disk filesystem information"""
        disk = psutil.disk_usage('/')
        output = f"Filesystem     Size      Used     Avail    Use%\n"
        output += f"root      {disk.total:10d} {disk.used:10d} {disk.free:10d}  {disk.percent:3.0f}%\n"
        return (output, "", cwd, 0)

    def _stat(self, args: List[str], cwd: str):
        """Display file status"""
        if not args:
            return ("", "stat: missing file operand\n", cwd, 2)
        
        filepath = args[0]
        p = self._path_resolve(filepath, cwd)
        
        if not os.path.exists(p):
            return ("", f"stat: {filepath}: No such file or directory\n", cwd, 1)
        
        stat_info = os.stat(p)
        output = f"  File: {filepath}\n"
        output += f"  Size: {stat_info.st_size}\n"
        output += f"  Mode: {oct(stat_info.st_mode)}\n"
        output += f"Access: {datetime.fromtimestamp(stat_info.st_atime).strftime('%Y-%m-%d %H:%M:%S')}\n"
        output += f"Modify: {datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n"
        output += f"Change: {datetime.fromtimestamp(stat_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return (output, "", cwd, 0)

    def _chmod(self, args: List[str], cwd: str):
        """Change file permissions"""
        if len(args) < 2:
            return ("", "chmod: missing operands\n", cwd, 2)
        
        mode_str = args[0]
        filepath = args[1]
        
        try:
            mode = int(mode_str, 8)
        except ValueError:
            return ("", f"chmod: invalid mode: '{mode_str}'\n", cwd, 1)
        
        p = self._path_resolve(filepath, cwd)
        if not os.path.exists(p):
            return ("", f"chmod: {filepath}: No such file or directory\n", cwd, 1)
        
        try:
            os.chmod(p, mode)
            return ("", "", cwd, 0)
        except Exception as e:
            return ("", f"chmod: error: {e}\n", cwd, 1)

    def _date(self, args: List[str], cwd: str):
        """Display current date and time"""
        now = datetime.now()
        return (now.strftime("%a %b %d %H:%M:%S %Y\n"), "", cwd, 0)

    def _uptime(self):
        """Display system uptime"""
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return (f"up {days} days, {hours}:{minutes:02d}\n", "", None, 0)

    def _whoami(self, cwd: str):
        """Display current user"""
        import getpass
        return (getpass.getuser() + "\n", "", cwd, 0)

    def _hostname(self, cwd: str):
        """Display hostname"""
        import socket
        return (socket.gethostname() + "\n", "", cwd, 0)

    def _md5sum(self, args: List[str], cwd: str):
        """Calculate MD5 checksum"""
        if not args:
            return ("", "md5sum: missing file operand\n", cwd, 2)
        
        results = []
        for filepath in args:
            p = self._path_resolve(filepath, cwd)
            if not os.path.exists(p):
                return ("", f"md5sum: {filepath}: No such file or directory\n", cwd, 1)
            if os.path.isdir(p):
                return ("", f"md5sum: {filepath}: Is a directory\n", cwd, 1)
            
            md5_hash = hashlib.md5()
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            results.append(f"{md5_hash.hexdigest()}  {filepath}")
        
        return ("\n".join(results) + "\n", "", cwd, 0)

    def _sha256sum(self, args: List[str], cwd: str):
        """Calculate SHA256 checksum"""
        if not args:
            return ("", "sha256sum: missing file operand\n", cwd, 2)
        
        results = []
        for filepath in args:
            p = self._path_resolve(filepath, cwd)
            if not os.path.exists(p):
                return ("", f"sha256sum: {filepath}: No such file or directory\n", cwd, 1)
            if os.path.isdir(p):
                return ("", f"sha256sum: {filepath}: Is a directory\n", cwd, 1)
            
            sha256_hash = hashlib.sha256()
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            results.append(f"{sha256_hash.hexdigest()}  {filepath}")
        
        return ("\n".join(results) + "\n", "", cwd, 0)

    def _clear(self, cwd: str):
        """Clear screen (simulated)"""
        return ("\n" * 50, "", cwd, 0)

    def _which(self, args: List[str], cwd: str):
        """Show which command would be executed"""
        if not args:
            return ("", "which: missing command\n", cwd, 2)
        
        cmd = args[0]
        supported_commands = [
            "pwd", "ls", "cd", "mkdir", "rm", "rmdir", "cat", "touch", 
            "mv", "cp", "echo", "cpu", "mem", "ps", "head", "tail", 
            "wc", "grep", "find", "tree", "du", "df", "stat", "chmod",
            "date", "uptime", "whoami", "hostname", "md5sum", "sha256sum",
            "clear", "which", "help"
        ]
        
        if cmd in supported_commands:
            return (f"/usr/bin/{cmd}\n", "", cwd, 0)
        else:
            return ("", f"which: no {cmd} in built-in commands\n", cwd, 1)

    def _help_text(self):
        return (
            "Supported commands:\n"
            "File Operations:\n"
            "  pwd                          - Print working directory\n"
            "  ls [-l] [-a] [path]          - List directory contents\n"
            "  cd <path>                    - Change directory\n"
            "  mkdir <name>                 - Create directory\n"
            "  rmdir <name>                 - Remove empty directory\n"
            "  rm [-r] <path>               - Remove file or directory\n"
            "  cat <file>                   - Display file contents\n"
            "  touch <file>                 - Create empty file or update timestamp\n"
            "  mv <src> <dest>              - Move/rename files\n"
            "  cp [-r] <src> <dest>         - Copy files or directories\n"
            "  head [-n num] <file>         - Display first lines of file (default 10)\n"
            "  tail [-n num] <file>         - Display last lines of file (default 10)\n"
            "  wc <file>                    - Count lines, words, characters\n"
            "  grep <pattern> <file>        - Search for pattern in file\n"
            "  find [path] [-name pattern]  - Find files matching pattern\n"
            "\n"
            "File Information:\n"
            "  stat <file>                  - Display file status and metadata\n"
            "  chmod <mode> <file>          - Change file permissions (octal)\n"
            "  du [path]                    - Display disk usage\n"
            "  df                           - Display filesystem disk space\n"
            "  tree [path]                  - Display directory tree structure\n"
            "  md5sum <file>                - Calculate MD5 checksum\n"
            "  sha256sum <file>             - Calculate SHA256 checksum\n"
            "\n"
            "Text Output:\n"
            "  echo [text]                  - Print text to stdout\n"
            "  echo [text] > file           - Write text to file (overwrite)\n"
            "  echo [text] >> file          - Append text to file\n"
            "  cat <file>                   - Display file contents\n"
            "  cat > file                   - Write input to file (empty line to end)\n"
            "  cat >> file                  - Append input to file (empty line to end)\n"
            "  cat >> file << EOF           - Heredoc: write until EOF is entered\n"
            "\n"
            "System Information:\n"
            "  cpu                          - Display CPU usage\n"
            "  mem                          - Display memory usage\n"
            "  ps                           - List running processes\n"
            "  date                         - Display current date and time\n"
            "  uptime                       - Display system uptime\n"
            "  whoami                       - Display current user\n"
            "  hostname                     - Display system hostname\n"
            "\n"
            "Utilities:\n"
            "  clear                        - Clear screen\n"
            "  which <cmd>                  - Show command location\n"
            "  help                         - Display this help message\n"
        )