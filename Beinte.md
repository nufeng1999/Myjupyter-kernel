## Behavior interpreter (行为解释器)

### 1.保存内容

#### 1.保存前做什么

##### 相关宏标签

###### include

包含指定的文件内容
###### discleannotes

不清除注释，默认生成代码时清除注释内容
###### srvmode

srvmode: tcp://0.0.0.0:xxx 设置并启动rpc通信服务
###### srvurl

为客户端设置rpc通信服务地址
###### cleartest

清除测试区的内容
###### cwd

设置当前代码工作的路径
###### loadurl

从网上加载内容
###### fileencode

指定生成文件时的文件编码
###### onlycsfile

仅生成代码文件，不编译不运行
###### overwritefile

覆盖已经存在的文件，配合file标签使用
###### onlyruncmd

仅运行特殊标签的内容，不生成代码文件，不运行代码
#### 2.保存后做什么

##### 相关宏标签

###### file & saveto

把代码保存到指定的文件中
###### filedict

多文件保存时，设置相关字典
###### filefordict

内容按字典进行保存
###### filelist

多文件保存时，设置相关列表
###### fileforlist

内容按列表进行保存
#### 提供哪些行为宏标签

##### dbglog

#### 提供哪些接囗

### 2.编译内容

 怎么编译  
#### 1.编译前做什么

##### 相关宏标签

###### ldflags

指定 gcc 连接参数
###### cflags

指定 gcc 编译参数
###### compile

指定编译器程序
#### 2.编译后做什么

##### 相关宏标签

#### 提供哪些接囗

### 3.执行内容

怎么执行

#### 1.执行前做什么

##### 相关宏标签

###### noruncode

不运行代码，仅生成代码文件
###### runinterm

代码执行在终端窗口中
###### term

指定终端程序，配合 runinterm 使用，linux 默认为gnome-term
###### fifo2stdin

###### runmode

执行代码运行的模式
###### rpcsrvfollowcode

设置 rpc 通信服务跟随代码执行结束而结束，否则一直等待通信消息，不自动退出。
###### runprg

设置代码按 runprg 配置的程序进行运行
###### runprgargs

runprg 配置的程序的启动参数
###### args

指定代码执行时的参数
###### outencode

代码执行后的输出内容的编码
###### outputtype

代码执行后的输出内容的mimetype，默认为标准 text
###### switches

###### options

###### coptions

###### joptions

###### replsetip

###### replchildpid

###### pidcmd

###### replsetip

#### 2.执行中做什么

##### 相关宏标签

###### stdin<-

将共享内存通信通道的内容转发到标准输入 stdin 中。格式 stdin<-:namexxx
#### 3.执行后做什么

##### 相关宏标签

###### assfile

代码执行结束后，仅跟随运行的关联文件 ipynb num ,格式为ipynb文件名+空格+cell编号
###### sendrpcmsg

发送的rpc通信消息
格式 sendrpcmsg:tcp://127.0.0.1:xxx 文本消息内容
###### srmafterexec

代码完全执行结束后，发送的rpc通信消息
格式 srmafterexec:tcp://127.0.0.1:xxx 文本消息内容
###### smafterexec

代码完全执行结束后，发送的共享内存通信消息
###### stdout2fifo

###### stdout->

stdout->:namexxx，将标准输出内容发送到共享内存通信通道。
#### 提供哪些接囗

### 4.其它

#### 1.日志

##### 相关宏标签

###### log

输出记录日志的等级，0，1，2
#### 2.通信

##### 相关宏标签

###### stoprpcsrv

发送给rpc服务的停止服务的命令
###### sendrpcmsg

发送给rpc服务的消息指令
#### 其它行为

##### 相关宏标签

###### repllistpid

###### replcmdmode

###### replprompt

###### execfile

终端打开时运行的文件
###### env

代码运行时的环境变量
###### rungdb

###### showpid

###### define

定义一个宏
###### test

###### cargo

###### dart

###### flutter

###### npm

###### pub

###### pycmd

###### cmd

执行shell命令
###### swift

###### templatefile

装入jj2格式模板文件
###### jj2模板区

##jj2_being 和 ##jj2_end 之间的内容为模板内容
//jj2_being 和 //jj2_end 为兼容格式
###### 测试区

##test_being 和 ##test_end 之间的内容为测试区内容
//test_being 和 //test_end 为兼容格式
#### 其它接口

### 5.常用标签

overwritefile,file,noruncode,include
内容描述
内容管理
获取内容
内容文件名
内容分类

代码编译器
代码执行器

#内容预处理器  
[参考](https://)ffgsgf

    预处理实现方式：
    python 提供了eval()函数和exec()函数
    eval()函数只能计算单个表达式的值，而exec()函数可以动态运行代码段。
    eval()函数可以有返回值，而exec()函数返回值永远为None。
    可以通过判断globals()函数的返回值中是否包含某个key来判断，某个全局变量是否已经存在（被定义）
    compile函数，将source编译为code对象或AST对象。code对象能够通过exec()函数来执行或者通过eval()函数进行计算求值。
    [参考地址](https://www.cnblogs.com/yyds/p/6276746.html)

    1.分离逻辑运算行和源代码行
        'if','ifdef','ifndef','elif','else','endif','defined'
        之间插入函数A，A(行,bool) 对si里的记录做标记

    li表 放入分离出的宏逻辑行
    li表格式：
    |content|linenum                      |
    |逻辑行  |行内包含的内容行 2，3，4，5......|
    |结束符  |空                            |
    si表 放入非逻辑行内容
    |content|linenum| 是否剔除 |
    |原始内容|1      |         |
    
    2.根据逻辑行计算结果获得 si 的内容
    或从si里剔除不需要的内容
    3.最后最新得到逻辑计算后的整个内容

            


    #define            定义一个预处理宏
    #undef            取消宏的定义

    #if                   编译预处理中的条件命令，相当于C语法中的if语句
    #ifdef              判断某个宏是否被定义，若已定义，执行随后的语句
    #ifndef            与#ifdef相反，判断某个宏是否未被定义
    #elif                若#if, #ifdef, #ifndef或前面的#elif条件不满足，则执行#elif之后的语句，相当于C语法中的else-if
    #else              与#if, #ifdef, #ifndef对应, 若这些条件不满足，则执行#else之后的语句，相当于C语法中的else
    #endif             #if, #ifdef, #ifndef这些条件命令的结束标志.
    defined         　与#if, #elif配合使用，判断某个宏是否被定义



