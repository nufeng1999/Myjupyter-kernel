from math import exp
from queue import Queue
from threading import Thread
from ipykernel.kernelbase import Kernel
from pexpect import replwrap, EOF
from jinja2 import Environment, PackageLoader, select_autoescape,Template
import pexpect
import signal
import typing 
import typing as t
import re
import signal
import subprocess
import tempfile
import os
import sys
import traceback
import os.path as path
import codecs
import time
import importlib
import importlib.util
import inspect
class IREPLWrapper(replwrap.REPLWrapper):
    def __init__(self, write_to_stdout, write_to_stderr, read_from_stdin,
                cmd_or_spawn,replsetip, orig_prompt, prompt_change,
                extra_init_cmd=None, line_output_callback=None):
        self._write_to_stdout = write_to_stdout
        self._write_to_stderr = write_to_stderr
        self._read_from_stdin = read_from_stdin
        self.line_output_callback = line_output_callback
        self.replsetip=replsetip
        self.startflag=True
        self.startexpecttimeout=60
        self.start_time = time.time()
        replwrap.REPLWrapper.__init__(self, cmd_or_spawn, orig_prompt,
                                      prompt_change,extra_init_cmd=extra_init_cmd)
    def _expect_prompt(self, timeout=-1):
        if timeout == -1 or timeout ==None :
            retry=0
            received=False
            cmdstart_time = time.time()
            cmdexectimeout=10
            while True:
                if self.startflag :
                    cmdexectimeout=None
                    run_time = time.time() - self.start_time
                    if run_time > self.startexpecttimeout:
                        self.startflag=False
                        self.line_output_callback(self.child.before + '\r\n')
                        self.line_output_callback("\n0End of startup process\n")
                        break
                try:
                    pos = self.child.expect_exact([u'\r\n', self.continuation_prompt, self.replsetip, pexpect.EOF, pexpect.TIMEOUT],timeout=cmdexectimeout)
                    if pos == 2:
                        if self.child.terminated:
                            self.line_output_callback("\nprocess.terminated\n")
                        self.line_output_callback(self.child.before +self.replsetip+ '\r\n')
                        self.line_output_callback("\nEnd of startup process\n")
                        self.replsetip=u'\r\n'
                        cmdexectimeout=None
                        self.startflag=False
                        break
                    elif pos ==3:
                        if len(self.child.before) != 0:
                            self.line_output_callback(self.child.before + '\r\n')
                        self.line_output_callback('The process has exited.\r\n')
                        break
                    elif pos == 0:
                        self.line_output_callback(self.child.before + '\n')
                        cmdstart_time = time.time()
                    else:
                        if len(self.child.before) != 0:
                            self.line_output_callback(self.child.before)
                            cmdstart_time = time.time()
                        else:
                            if self.startflag :
                                continue
                            run_time = time.time() - cmdstart_time
                            if run_time > 10:
                                break
                except Exception as e:
                    self._write_to_stderr("[MyPythonkernel] Error:Executable _expect_prompt error! "+str(e)+"\n")
        else:
            pos = replwrap.REPLWrapper._expect_prompt(self, timeout=timeout)
        return pos
class RealTimeSubprocess(subprocess.Popen):
    inputRequest = "<inputRequest>"
    def __init__(self, cmd, write_to_stdout, write_to_stderr, read_from_stdin,cwd=None,shell=False,env=None):
        self._write_to_stdout = write_to_stdout
        self._write_to_stderr = write_to_stderr
        self._read_from_stdin = read_from_stdin
        super().__init__(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE,
                            bufsize=0,cwd=cwd,shell=shell,env=env)
        self._stdout_queue = Queue()
        self._stdout_thread = Thread(target=RealTimeSubprocess._enqueue_output, args=(self.stdout, self._stdout_queue))
        self._stdout_thread.daemon = True
        self._stdout_thread.start()
        self._stderr_queue = Queue()
        self._stderr_thread = Thread(target=RealTimeSubprocess._enqueue_output, args=(self.stderr, self._stderr_queue))
        self._stderr_thread.daemon = True
        self._stderr_thread.start()
    @staticmethod
    def _enqueue_output(stream, queue):
        for line in iter(lambda: stream.read(4096), b''):
            queue.put(line)
        stream.close()
    def write_contents(self,magics=None):
        def read_all_from_queue(queue):
            res = b''
            size = queue.qsize()
            while size != 0:
                res += queue.get_nowait()
                size -= 1
            return res
        stderr_contents = read_all_from_queue(self._stderr_queue)
        if stderr_contents:
            self._write_to_stderr(stderr_contents.decode())
        stdout_contents = read_all_from_queue(self._stdout_queue)
        if stdout_contents:
            contents = stdout_contents.decode()
            start = contents.find(self.__class__.inputRequest)
            if(start >= 0):
                contents = contents.replace(self.__class__.inputRequest, '')
                if(len(contents) > 0):
                    self._write_to_stdout(contents,magics)
                readLine = ""
                while(len(readLine) == 0):
                    readLine = self._read_from_stdin()
                readLine += "\n"
                self.stdin.write(readLine.encode())
            else:
                self._write_to_stdout(contents,magics)
class MyPythonKernel(Kernel):
    implementation = 'jupyter-MyPython-kernel'
    implementation_version = '1.0'
    language = 'Python'
    language_version = sys.version.split()[0]
    language_info = {'name': 'python',
                     'version': sys.version.split()[0],
                     'mimetype': 'text/x-python',
                     'codemirror_mode': {
                        'name': 'ipython',
                        'version': sys.version_info[0]
                     },
                     'pygments_lexer': 'ipython%d' % 3,
                     'nbconvert_exporter': 'python',
                     'file_extension': '.py'}
    banner = "MyPython kernel.\n" \
             "Uses gcc, compiles in C11, and creates source code files and executables in temporary folder.\n"
    kernelinfo="[MyPython]"
    main_head = "\n" \
            "\n" \
            "int main(List<String> arguments){\n"
    main_foot = "\nreturn 0;\n}"
    plugins={"0":[],
         "1":[],
         "2":[],
         "3":[],
         "4":[],
         "5":[],
         "6":[],
         "7":[],
         "8":[],
         "9":[]}
    silent=None
    jinja2_env = Environment()
    g_rtsps={}
    g_chkreplexit=True
    def __init__(self, *args, **kwargs):
        super(MyPythonKernel, self).__init__(*args, **kwargs)
        self._allow_stdin = True
        self.readOnlyFileSystem = False
        self.bufferedOutput = True
        self.linkMaths = True # always link math library
        self.wAll = True # show all warnings by default
        self.wError = False # but keep comipiling for warnings
        self.files = []
        self.resDir = path.join(path.dirname(path.realpath(__file__)), 'resources')
        self.chk_replexit_thread = Thread(target=self.chk_replexit, args=(self.g_rtsps))
        self.chk_replexit_thread.daemon = True
        self.chk_replexit_thread.start()
    isjj2code=False
    def _is_jj2_begin(self,line):
        if line==None or line=='':return ''
        return line.strip().startswith('##jj2_begin') or line.strip().startswith('//jj2_begin')
    def _is_jj2_end(self,line):
        if line==None or line=='':return ''
        return line.strip().startswith('##jj2_end') or line.strip().startswith('//jj2_end')
    jj2code_cache=[]
    jj2code_args={}
    def cleanjj2code_cache(self,):
        self.jj2code_cache.clear()
        self.jj2code_args={}
    def addjj2codeline(self,line):
        self.jj2code_cache+=[line]
    def getjj2code(self):
        if len(self.jj2code_cache)<1:return ''
        code=''.join(line+'\n' for line in self.jj2code_cache)
        return code
    def execjj2code_cache(self) -> str:
        code=self.getjj2code()
        if code==None or code.strip()=='': return code
        env = Environment()
        template = Template(code)
        ret=template.render(self.jj2code_args)
        return ret
    def forcejj2code(self,line): 
        if not self.isjj2code:
            istb=self._is_jj2_begin(line)
            if istb: 
                self.isjj2code=True
                if len(line.strip())>15:
                    argline =line.split(":",1)
                    if len(argline)>1:
                        argstr=argline[1]
                        tplargs=self._filter_dict(argstr)
                        self.jj2code_args.update(tplargs)
                    iste=self._is_jj2_end(line)
                    if iste:
                        self.cleanjj2code_cache()
                        self.isjj2code=False
                        return ''
                line= ''
        iste=self._is_jj2_end(line)
        if iste:
            self.isjj2code=False
            line= ''
            line=self.execjj2code_cache()
            self.cleanjj2code_cache()
            return line
        if self.isjj2code: self.addjj2codeline(line)
        line= "" if self.isjj2code else line+"\n"
        return line
    def readtemplatefile(self,filename,spacecount=0,*args: t.Any, **kwargs: t.Any):
        filecode=''
        newfilecode=''
        codelist1=None
        filenm=os.path.join(os.path.abspath(''),filename);
        if not os.path.exists(filenm):
            return filecode;
        template = self.jinja2_env.get_template(filenm)
        filecode=template.render(*args,**kwargs)
        for line in filecode.splitlines():
            if len(line)>0:
                for t in line:
                    newfilecode+=' '*spacecount + t+'\n'
        return newfilecode
    def _is_test_begin(self,line):
        if line==None or line=='':return ''
        return line.strip().startswith('##test_begin') or line.strip().startswith('//test_begin')
    def _is_test_end(self,line):
        if line==None or line=='':return ''
        return line.strip().startswith('##test_end') or line.strip().startswith('//test_end')
    def _is_dqm_begin(self,line):
        if line==None or line=='':return ''
        return line.lstrip().startswith('\"\"\"')
    def _is_dqm_end(self,line):
        if line==None or line=='':return ''
        return line.rstrip().endswith('\"\"\"')
    def _is_sqm_begin(self,line):
        if line==None or line=='':return ''
        return line.lstrip().startswith('\'\'\'')
    def _is_sqm_end(self,line):
        if line==None or line=='':return ''
        return line.rstrip().endswith('\'\'\'')
    def cleannotes(self,line):
        return '' if (not self._is_specialID(line)) and (line.lstrip().startswith('#') or line.lstrip().startswith('//')) else line
    isdqm=False
    def cleandqm(self,line):
        if not self.isdqm:
            istb=self._is_dqm_begin(line)
            if istb: 
                self.isdqm=True
                if len(line.strip())>5:
                    iste=self._is_dqm_end(line)
                    if iste:self.isdqm=False
                return ''
        iste=self._is_dqm_end(line)
        if iste:
            self.isdqm=False
            return ''
        line= "" if self.isdqm else line
        return line
    issqm=False
    def cleansqm(self,line):
        if not self.issqm:
            istb=self._is_sqm_begin(line)
            if istb: 
                self.issqm=True
                if len(line.strip())>5:
                    iste=self._is_sqm_end(line)
                    if iste:self.issqm=False
                return ''
        iste=self._is_sqm_end(line)
        if iste:
            self.issqm=False
            return ''
        line= "" if self.issqm else line
        return line
    istestcode=False
    def cleantestcode(self,line):
        if not self.istestcode:
            istb=self._is_test_begin(line)
            if istb: 
                self.istestcode=True
                if len(line.strip())>5:
                    iste=self._is_test_end(line)
                    if iste:self.istestcode=False
                return ''
        iste=self._is_test_end(line)
        if iste:
            self.istestcode=False
            return ''
        line= "" if self.istestcode else line
        return line
    usleep = lambda x: time.sleep(x/1000000.0)
    def replacemany(self,our_str, to_be_replaced:str, replace_with:str):
        while (to_be_replaced in our_str):
            our_str = our_str.replace(to_be_replaced, replace_with)
        return our_str
    def _filter_dict(self,argsstr):
        if not argsstr or len(argsstr.strip())<1:
            return None
        env_dict={}
        argsstr=self.replacemany(self.replacemany(self.replacemany(argsstr.strip(),('  '),' '),('= '),'='),' =','=')
        pattern = re.compile(r'([^\s*]*)="(.*?)"|([^\s*]*)=(\'.*?\')|([^\s*]*)=(.[^\s]*)')
        env_list=envstr.split(",")
        for i in range(0,len(env_list),2):
            env_dict[str(env_list[i])]=env_list[i+1]
        return env_dict
    def _is_specialID(self,line):
        if line.strip().startswith('##%') or line.strip().startswith('//%'):
            return True
        return False
    def repl_listpid(self):
        if len(self.g_rtsps)>0: 
            self._write_to_stdout("--------All replpid--------\n")
            for key in self.g_rtsps:
                self._write_to_stdout(key+"\n")
        else:
            self._write_to_stdout("--------All replpid--------\nNone\n")
    def chk_replexit(grtsps): 
        while MyPythonKernel.g_chkreplexit:
            try:
                if len(grtsps)>0: 
                    for key in grtsps:
                        if grtsps[key].child.terminated:
                            pass
                            del grtsps[key]
            finally:
                pass
        if len(grtsps)>0: 
            for key in grtsps:
                if grtsps[key].child.terminated:
                    pass
                    del grtsps[key]
                else:
                    grtsps[key].child.terminate(force=True)
                    del grtsps[key]
    def cleanup_files(self):
        for file in self.files:
            if(os.path.exists(file)):
                os.remove(file)
    def new_temp_file(self, **kwargs):
        kwargs['delete'] = False
        kwargs['mode'] = 'w'
        file = tempfile.NamedTemporaryFile(**kwargs)
        self.files.append(file.name)
        return file
    def _log(self, output,level=1,outputtype='text/plain'):
        streamname='stdout'
        if not self.silent:
            prestr=self.kernelinfo+' Info:'
            if level==2:
                prestr=self.kernelinfo+' Warning:'
                streamname='stderr'
            elif level==3:
                prestr=self.kernelinfo+' Error:'
                streamname='stderr'
            else:
                prestr=self.kernelinfo+' Info:'
                streamname='stdout'
            if len(outputtype)>0 and (level!=2 or level!=3):
                self._write_display_data(mimetype=outputtype,contents=prestr+output)
                return
            stream_content = {'name': streamname, 'text': prestr+output}
            self.send_response(self.iopub_socket, 'stream', stream_content)
    def _write_display_data(self,mimetype='text/html',contents=""):
        self.send_response(self.iopub_socket, 'display_data', {'data': {mimetype:contents}, 'metadata': {mimetype:{}}})
    def _write_to_stdout(self,contents,magics=None):
        if magics !=None and len(magics['outputtype'])>0:
            self._write_display_data(mimetype=magics['outputtype'],contents=contents)
        else:
            self.send_response(self.iopub_socket, 'stream', {'name': 'stdout', 'text': contents})
    def _write_to_stderr(self, contents):
        self.send_response(self.iopub_socket, 'stream', {'name': 'stderr', 'text': contents})
    def _read_from_stdin(self):
        return self.raw_input()
    def readcodefile(self,filename,spacecount=0):
        filecode=''
        codelist1=None
        if not os.path.exists(filename):
            return ''
        with open(os.path.join(os.path.abspath(''),filename), 'r') as codef1:
            codelist1 = codef1.readlines()
        if len(codelist1)>0:
            for t in codelist1:
                filecode+=' '*spacecount + t
        return filecode
    def _start_replprg(self,command,args,magics):
        sig = signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.silent = None
        try:
            child = pexpect.spawn(command, args,timeout=60, echo=False,
                                  encoding='utf-8')
            self._write_to_stdout("replchild pid:"+str(child.pid)+"\n")
            self._write_to_stdout("--------process info---------\n")
            self.replwrapper = IREPLWrapper(
                                    self._write_to_stdout,
                                    self._write_to_stderr,
                                    self._read_from_stdin,
                                    child,
                                    replsetip=magics['replsetip'],
                                    orig_prompt='\r\n', 
                                    prompt_change=None,
                                    extra_init_cmd=None,
                                    line_output_callback=self.process_output)
            self.g_rtsps[str(self.replwrapper.child.pid)]=self.replwrapper
        except Exception as e:
            self._write_to_stderr("[MyPythonkernel] Error:Executable _start_replprg error! "+str(e)+"\n")
        finally:
            signal.signal(signal.SIGINT, sig)
    def process_output(self, output,magics=None):
        if not self.silent:
            if magics !=None and len(magics['outputtype'])>0:
                self._write_display_data(mimetype=magics['outputtype'],contents=output)
                return
            stream_content = {'name': 'stdout', 'text': output}
            self.send_response(self.iopub_socket, 'stream', stream_content)
    def send_replcmd(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=False,magics=None):
        self.silent = silent
        if not code.strip():
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}
        interrupted = False
        try:
            self._write_to_stdout("send replcmd:"+code.rstrip()+"\n")
            self._write_to_stdout("---Received information after send repl cmd---\n")
            if magics and len(magics['replchildpid'])>0 :
                if self.g_rtsps[magics['replchildpid']] and \
                    self.g_rtsps[magics['replchildpid']].child and \
                    not self.g_rtsps[magics['replchildpid']].child.terminated :
                    self.g_rtsps[magics['replchildpid']].run_command(code.rstrip(), timeout=None)
            else:
                if self.replwrapper and \
                    self.replwrapper.child and \
                    not self.replwrapper.child.terminated :
                    self.replwrapper.run_command(code.rstrip(), timeout=None)
            pass
        except KeyboardInterrupt:
            self.gdbwrapper.child.sendintr()
            interrupted = True
            self.gdbwrapper._expect_prompt()
            output = self.gdbwrapper.child.before
            self.process_output(output)
        except EOF:
            pass
        if interrupted:
            return {'status': 'abort', 'execution_count': self.execution_count}
        exitcode = 0
        if exitcode:
            error_content = {'execution_count': self.execution_count,
                             'ename': '', 'evalue': str(exitcode), 'traceback': []}
            self.send_response(self.iopub_socket, 'error', error_content)
            error_content['status'] = 'error'
            return error_content
        else:
            return {'status': 'ok', 'execution_count': self.execution_count,
                    'payload': [], 'user_expressions': {}}
    def do_shell_command(self,commands,cwd=None,shell=True,env=True,magics=None):
        try:
            if len(magics['replcmdmode'])>0:
                findObj= commands[0].split(" ",1)
                if findObj and len(findObj)>1:
                    cmd=findObj[0]
                    arguments=findObj[1]
                    cmdargs=[]
                    for argument in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', arguments):
                        cmdargs += [argument.strip('"')]
                    self._write_to_stdout(cmd)
                    self._write_to_stdout(''.join((' '+ str(s) for s in cmdargs))+"\n")
                    self._start_replprg(cmd,cmdargs,magics)
                    return
            p = RealTimeSubprocess(commands,
                                  self._write_to_stdout,
                                  self._write_to_stderr,
                                  self._read_from_stdin,cwd,shell,env=env)
            self.g_rtsps[str(p.pid)]=p
            if magics!=None and len(magics['showpid'])>0:
                self._write_to_stdout("The process PID:"+str(p.pid)+"\n")
            while p.poll() is None:
                p.write_contents()
            p._stdout_thread.join()
            p._stderr_thread.join()
            del self.g_rtsps[str(p.pid)]
            p.write_contents()
            if p.returncode != 0:
                self._write_to_stderr("[MyPythonkernel] Error: Executable command exited with code {}\n".format(p.returncode))
            else:
                self._write_to_stdout("[MyPythonkernel] Info: command success.\n")
            return
        except Exception as e:
            self._write_to_stderr("[MyPythonkernel] Error:Executable command error! "+str(e)+"\n")
    def do_Py_command(self,commands=None,cwd=None,magics=None):
        p = self.create_jupyter_subprocess(['MyPythonKernel']+commands,cwd=os.path.abspath(''),shell=False)
        self.g_rtsps[str(p.pid)]=p
        if magics!=None and len(magics['showpid'])>0:
            self._write_to_stdout("The process PID:"+str(p.pid)+"\n")
        while p.poll() is None:
            p.write_contents()
        p._stdout_thread.join()
        p._stderr_thread.join()
        del self.g_rtsps[str(p.pid)]
        p.write_contents()
        if p.returncode != 0:
            self._write_to_stderr("[MyPythonkernel] Executable exited with code {}".format(p.returncode))
        else:
            self._write_to_stdout("[MyPythonkernel] Info:MyPythonKernel command success.")
        return
    def do_flutter_command(self,commands=None,cwd=None,magics=None):
        p = self.create_jupyter_subprocess(['flutter']+commands,cwd=os.path.abspath(''),shell=False)
        self.g_rtsps[str(p.pid)]=p
        if magics!=None and len(magics['showpid'])>0:
            self._write_to_stdout("The process PID:"+str(p.pid)+"\n")
        while p.poll() is None:
            p.write_contents()
        p._stdout_thread.join()
        p._stderr_thread.join()
        del self.g_rtsps[str(p.pid)]
        p.write_contents()
        if p.returncode != 0:
            self._write_to_stderr("[MyPythonkernel] Executable exited with code {}".format(p.returncode))
        else:
            self._write_to_stdout("[MyPythonkernel] Info:flutter command success.")
        return
    def send_cmd(self,pid,cmd):
        try:
            self.g_rtsps[pid]._write_to_stdout(cmd)
        except Exception as e:
            self._write_to_stderr("[MyPythonkernel] Error:Executable send_cmd error! "+str(e)+"\n")
        return
    def create_jupyter_subprocess(self, cmd,cwd=None,shell=False,env=None):
        try:
            return RealTimeSubprocess(cmd,
                                  self._write_to_stdout,
                                  self._write_to_stderr,
                                  self._read_from_stdin,cwd,shell,env)
        except Exception as e:
            self._write_to_stdout("RealTimeSubprocess err:"+str(e))
            raise
    def generate_Pythonfile(self, source_filename, binary_filename, cflags=None, ldflags=None):
        return
    def _filter_env(self, envstr):
        if envstr is None or len(envstr.strip())<1:
            return os.environ
        envstr=str(str(envstr.split("|")).split("=")).replace(" ","").replace("\'","").replace("\"","").replace("[","").replace("]","").replace("\\","")
        env_list=envstr.split(",")
        for i in range(0,len(env_list),2):
            os.environ.setdefault(env_list[i],env_list[i+1])
        return os.environ
    def _filter_magics(self, code):
        magics = {
                  'file': [],
                  'overwritefile': [],
                  'include': [],
                  'templatefile': [],
                  'repllistpid': [],
                  'replcmdmode': [],
                  'replprompt': [],
                  'replsetip': "\r\n",
                  'replchildpid':"0",
                  'showpid': [],
                  'norunnotecmd': [],
                  'noruncode': [],
                  'command': [],
                  'pythoncmd': [],
                  'outputtype':'text/plain',
                  'env':None,
                  'runmode': [],
                  'pid': [],
                  'pidcmd': [],
                  'args': []}
        actualCode = ''
        newactualCode = ''
        for line in code.splitlines():
            orgline=line
            line=self.forcejj2code(line)
            if line==None or line.strip()=='': continue
            if self._is_specialID(line):
                if line.strip()[3:] == "noruncode":
                    magics['noruncode'] += ['true']
                    continue
                elif line.strip()[3:] == "overwritefile":
                    magics['overwritefile'] += ['true']
                    continue
                elif line.strip()[3:] == "showpid":
                    magics['showpid'] += ['true']
                    continue
                elif line.strip()[3:] == "repllistpid":
                    magics['repllistpid'] += ['true']
                    self.repl_listpid()
                    continue
                elif line.strip()[3:] == "replcmdmode":
                    magics['replcmdmode'] += ['replcmdmode']
                    continue
                elif line.strip()[3:] == "replprompt":
                    magics['replprompt'] += ['replprompt']
                    continue
                elif line.strip()[3:] == "onlyrunnotecmd":
                    magics['onlyrunnotecmd'] += ['true']
                    continue
                elif line.strip()[3:] == "onlyruncmd":
                    magics['onlyruncmd'] += ['true']
                    continue
                findObj= re.search( r':(.*)',line)
                if not findObj or len(findObj.group(0))<2:
                    continue
                key, value = line.strip()[3:].split(":", 2)
                key = key.strip().lower()
                if key == "runmode":
                    if len(value)>0:
                        magics[key] = value[re.search(r'[^/]',value).start():]
                    else:
                        magics[key] ='real'
                elif key == "file":
                    if len(value)>0:
                        magics[key] = value[re.search(r'[^/]',value).start():]
                    else:
                        magics[key] ='newfile'
                elif key == "include":
                    if len(value)>0:
                        magics[key] = value
                    else:
                        magics[key] =''
                        continue
                    if len(magics['include'])>0:
                        index1=line.find('##%')
                        line=self.readcodefile(magics['include'],index1)
                        actualCode += line + '\n'
                elif key == "templatefile":
                    index1=line.find('//%')
                    if len(value)>0:
                        magics[key] =value.split(" ",1)
                    else:
                        magics[key] =None
                        continue
                    templatefile=magics['templatefile'][0]
                    if len(magics['templatefile'])>1:
                        argsstr=magics['templatefile'][1]
                        templateargsdict=self._filter_dict(argsstr)
                    else:
                        templateargsdict=None
                    if len(magics['templatefile'])>0:
                        line=self.readtemplatefile(templatefile,index1,templateargsdict)
                        actualCode += line + '\n'
                elif key == "pidcmd":
                    magics['pidcmd'] = [value]
                    if len(magics['pidcmd'])>0:
                        findObj= value.split(",",1)
                        if findObj and len(findObj)>1:
                            pid=findObj[0]
                            cmd=findObj[1]
                            self.send_cmd(pid=pid,cmd=cmd)
                elif key == "replsetip":
                    magics['replsetip'] = value
                elif key == "replchildpid":
                    magics['replchildpid'] = value
                elif key == "command" or key == "cmd":
                    magics['command'] = [value]
                    if len(magics['command'])>0:
                        self.do_shell_command(magics['command'],env=magics['env'])
                elif key == "pythoncmd":
                    for flag in value.split():
                        magics[key] += [flag]
                    if len(magics['pythoncmd'])>0:
                        self.do_Py_command(magics['pythoncmd'],magics=magics)
                elif key == "env":
                    envdict=self._filter_env(value)
                    magics[key] =dict(envdict)
                elif key == "outputtype":
                    magics[key]=value
                elif key == "args":
                    for argument in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', value):
                        magics['args'] += [argument.strip('"')]
            else:
                actualCode += line + '\n'
        newactualCode=actualCode
        if len(magics['file'])>0 and len(magics['noruncode'])>0:
            newactualCode=''
            for line in actualCode.splitlines():
                line=self.cleantestcode(line)
                if line=='':continue
                line=self.cleandqm(line)
                if line=='':continue
                line=self.cleansqm(line)
                if self.cleannotes(line)=='':
                    continue
                else:
                    newactualCode += line + '\n'
        return magics, newactualCode
    def _add_main(self, magics, code):
        tmpCode = re.sub(r"//.*", "", code)
        tmpCode = re.sub(r"/\*.*?\*/", "", tmpCode, flags=re.M|re.S)
        x = re.search(r".*\s+main\s*\(", tmpCode)
        if not x:
            code = self.main_head + code + self.main_foot
            magics['cflags'] += ['-lm']
        return magics, code
    def do_execute(self, code, silent, store_history=True,
                   user_expressions=None, allow_stdin=True):
        try:
            self.silent = silent
            magics, code = self._filter_magics(code)
            if len(magics['replcmdmode'])>0:
                return self.send_replcmd(code, silent, store_history=True,
                    user_expressions=None, allow_stdin=False)
            if len(magics['noruncode'])>0 and ( len(magics['command'])>0 or len(magics['pythoncmd'])>0):
                return {'status': 'ok', 'execution_count': self.execution_count, 'payload': [], 'user_expressions': {}}
            with self.new_temp_file(suffix='.py',dir=os.path.abspath('')) as source_file:
                source_file.write(code)
                source_file.flush()
                newsrcfilename=source_file.name
                if len(magics['file'])>0:
                    newsrcfilename = magics['file']
                    newsrcfilename = os.path.join(os.path.abspath(''),newsrcfilename)
                    if os.path.exists(newsrcfilename):
                        if len(magics['overwritefile'])<1:
                            newsrcfilename +=".new.py"
                    if not os.path.exists(os.path.dirname(newsrcfilename)) :
                        os.makedirs(os.path.dirname(newsrcfilename))
                    os.rename(source_file.name,newsrcfilename)
                    self._write_to_stdout("[MyPythonkernel] Info:file "+ newsrcfilename +" created successfully\n")
            if len(magics['noruncode'])>0:
                return {'status': 'ok', 'execution_count': self.execution_count, 'payload': [], 'user_expressions': {}}
            self._write_to_stdout("The process :"+newsrcfilename+"\n")
            p = self.create_jupyter_subprocess(['python',newsrcfilename]+ magics['args'],cwd=None,shell=False,env=magics['env'])
            self.g_rtsps[str(p.pid)]=p
            if len(magics['showpid'])>0:
                self._write_to_stdout("The process PID:"+str(p.pid)+"\n")
            while p.poll() is None:
                p.write_contents(magics)
            self._write_to_stdout("The process end:"+str(p.pid)+"\n")
            p._stdout_thread.join()
            p._stderr_thread.join()
            p.write_contents(magics)
            self.cleanup_files()
            if p.returncode != 0:
                self._write_to_stderr("[MyPythonkernel] Executable exited with code {}".format(p.returncode))
        except Exception as e:
            self._write_to_stderr("[MyPythonkernel] Error "+str(e))
        return {'status': 'ok', 'execution_count': self.execution_count, 'payload': [], 'user_expressions': {}}
    def do_shutdown(self, restart):
        self.g_chkreplexit=False
        self.chk_replexit_thread.join()
        self.cleanup_files()