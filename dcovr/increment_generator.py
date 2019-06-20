#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, re
import json
import commands
import time
from HTMLParser import HTMLParser
from pprint import *
from jinja2 import Environment, FileSystemLoader

DEBUG = 1

def convert_filepath_coverage_filename(filepath,
        skip_prefix,
        append_prefix,
        postfix):
    # @filepath: full path of a file, such as 'src/dir1/dir1_1/func.cpp'
    filepath = filepath[len(skip_prefix):]
    filepath = filepath.replace("/", "_")
    gcovrfile = append_prefix + filepath + postfix
    return gcovrfile


def templates():
    templates_path = os.path.join(os.path.dirname(__file__), 'templates')
    return Environment(loader=FileSystemLoader(templates_path), autoescape=False, trim_blocks=True)


class GcovHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.uncovers = []
        self.covers = []
        self.islineNum = False
        self.meet_lineno_tag = False
        self.lineNum = 0
        self.example = '''
//未覆盖的行
    <tr>
    <td align="right" class="lineno"><pre>164</pre></td>
    <td align="right" class="linebranch"></td>
    <td align="right" class="linecount uncoveredLine"><pre></pre></td>
    <td align="left" class="src uncoveredLine"><pre>            assert((size_t)bean.bean_index_in_slice_ &lt; chunk.recalled_do_slice_list_[bean.slice_index_in_chunk_].beans_.size());</pre></td>
    </tr>

#覆盖的行
    <tr>
    <td align="right" class="lineno"><pre>130</pre></td>
    <td align="right" class="linebranch"></td>
    <td align="right" class="linecount coveredLine"><pre>40</pre></td>
    <td align="left" class="src coveredLine"><pre>        int index_in_reacalled_do_info = 0;</pre></td>
    </tr>

#不需要计算的行
    <tr>
    <td align="right" class="lineno"><pre>169</pre></td>
    <td align="right" class="linebranch"></td>
    <td align="right" class="linecount "><pre></pre></td>
    <td align="left" class="src "><pre>}</pre></td>
    </tr>

    <tr>
    <td align="right" class="lineno"><pre>170</pre></td>
    <td align="right" class="linebranch"></td>
    <td align="right" class="linecount "><pre></pre></td>
    <td align="left" class="src "><pre></pre></td>
    </tr>
'''

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            for a in attrs:
                if a == ('class', 'lineno'):
                    self.islineNum = True
                if a == ('class', 'linecount uncoveredLine'):
                    self.uncovers.append(self.lineNum)
                if a == ('class', 'linecount coveredLine'):
                    self.covers.append(self.lineNum)
        if tag == "pre":
            self.meet_lineno_tag = True

    def handle_data(self, data):
        if self.meet_lineno_tag and self.islineNum:
            try:
                self.lineNum = int(data)
            except:
                self.lineNum = -1

    def handle_endtag(self, tag):
        if tag == "td":
            self.islineNum = False
        if tag == "pre":
            self.meet_lineno_tag = False

class UTCover(object) :
    def __init__(self, since_commit, until_commit, report_dir, prefix, missing_prefix_dir, thresh, monitor="{}") :
        self.since = since_commit
        self.until = until_commit
        self.monitor = json.loads(monitor)
        self.report_dir = report_dir
        self.missing_prefix_dir = missing_prefix_dir
        self.prefix = prefix
        self.thresh = float(thresh)

    # get the changed files from 'since' to 'until': the cpp file. the relative path to git repo root.
    def get_changed_files(self):
        # self.since, self.until, self.monitor
        satus, output = commands.getstatusoutput("git diff --name-only %s %s" %(self.since, self.until))
        src_files = [f for f in output.split('\n')
                        if os.path.splitext(f)[1][1:] in ['c', 'cpp']]
        if DEBUG:
            pprint("<<<< The changed files begin:")
            pprint(src_files)
            pprint(">>>> The changed files end:")
        return src_files

    # 获取每个文件改动的行号:在最新版本中的行号
    def get_changed_lines(self, src_files):
        # self.since, self.until
        changes = {}
        if DEBUG:
            pprint("<<<< The changed lines(unused lines included) begin:")
        for f in src_files:
            satus, output = commands.getstatusoutput("git log --oneline %s..%s %s | awk '{print $1}'" %(self.since, self.until, f))
            commits = output.split('\n')
            pprint("contains commits:")
            pprint(commits)
            cmd = "git blame %s | grep -E '(%s)' | awk  -F' *|)' '{print $6}'" %(f, '|'.join(commits))
            pprint("getting changed lines by %s" % (cmd))
            satus, lines = commands.getstatusoutput(cmd)
            changes[f] = [ int(i) for i in lines.split('\n') if i.isdigit() ]
            if DEBUG:
                print("File:", f, " || changed lines:", changes[f])

        if DEBUG:
            pprint(">>>> The changed lines end.")
        return changes

    # get the HtmlParser for source file.
    def get_report_parser(self, f):
        f = convert_filepath_coverage_filename(f,
                self.missing_prefix_dir,
                self.prefix,
                ".html")
        gcovfile = os.path.join(self.report_dir, f)
        if not os.path.exists(gcovfile):
            pprint("failed to find html report for %s" % gcovfile)
            return None
        report_parser = GcovHTMLParser()
        report_parser.feed(open(gcovfile, 'r').read())
        return report_parser

    def get_recoverage_info(self, changes):
        # self.report_dir
        uncovers = {}
        lcov_changes = {}
        pprint("<<<< get_recoverage_info Begin.")
        for f, lines in changes.items():
            report_parser = self.get_report_parser(f)
            #处理html report
            if not report_parser:
                uncovers[f] = lines
                lcov_changes[f] = lines
                continue
            #空行/{}等不计入统计范围
            lcov_changes[f] = sorted(list(set(report_parser.uncovers + report_parser.covers) & set(lines)))
            if len(lcov_changes[f]) == 0:
                del lcov_changes[f]
                continue
            uncov_lines = list(set(report_parser.uncovers) & set(lines))
            uncovers[f] = sorted(uncov_lines)
            covered_lines = sorted( list(set(report_parser.covers) & set(lines)) )
            if DEBUG:
                print(f, "uncovers:", uncovers[f],  "||covers:", covered_lines, "changed_line_num:", len(lcov_changes[f]))
            report_parser.close()
        pprint(">>>> get_recoverage_info END.")
        return lcov_changes, uncovers

    # @files_coverage_info is a map, key is filename, value is a tuple with two number, changed lines and convered lines
    # changed num, covered num, changed details.
    def create_coverage_trs(self, files_coverage_info):
        if DEBUG:
            pprint("<<<< create_coverage_trs")
        tr_tpl = templates().get_template("delta_trs.html")
        trs = ''
        for f, v in files_coverage_info.items():
            if v[0] == 0:
                continue
            changed_line_list = v[2]
            if DEBUG:
                print("Files:", f, " ||covered/total:", v[1], "/", v[0], " || changed lines:", changed_line_list)
            gcov_filename = convert_filepath_coverage_filename(f,
                    self.missing_prefix_dir,
                    self.prefix,
                    ".html")
            gcovrfilepath = os.path.join(self.report_dir, gcov_filename)
            # mark the changed lines with background color of red from original report
            if os.path.exists(gcovrfilepath):
                s = ''
                source_pattern_str=r'<td align="right" class="lineno"><pre>\d+</pre></td>';
                p = re.compile(source_pattern_str)
                for line in open(gcovrfilepath, 'r').readlines():
                    ps = p.search(line)
                    if ps:
                        # modify its back ground
                        lineno = int(re.findall("\d+", line)[0])
                        if changed_line_list.count(lineno) == 1:
                            line = line.replace('class="lineno"', 'class="lineno" style="background:red"')
                            line = line.replace('<pre>', '<pre>NN  ')
                        else:
                            pass
                    else:
                        pass
                    s += line
                increment_filepath = os.path.join(self.report_dir, "new_"+gcov_filename)
                open(increment_filepath, 'w').write(s)
                cover_ratio = round(v[1] * 1.0 / v[0] * 100, 2)
                bar_color = "yellow"
                c_color = "yellow"
                if cover_ratio >= 90.0:
                    bar_color = "green"
                    c_color = "LightGreen"
                if cover_ratio < 75.0:
                    bar_color = "red"
                    c_color = "LightPink"
                trs += tr_tpl.render(source_file=f,
                        link_file="new_"+gcov_filename,
                        changed_lines=v[0],
                        covered_lines=v[1],
                        bar_color=bar_color,
                        c_color=c_color,
                        coverage=cover_ratio)
            else:
                print("no such file", gcovrfilepath)
        return trs

    # @uncovers: a map, key is file name, value is a list of uncovered lines.
    # @changes: a map, key is filename, value is a list containing changed lines.
    def create_report(self, changes, uncovers):
        pprint("<<<< create_report")
        change_linenum, uncov_linenum = 0, 0
        for k, v in changes.items():
            change_linenum += len(v)
        for k, v in uncovers.items():
            uncov_linenum += len(v)

        cov_linenum = change_linenum - uncov_linenum
        coverage = round(cov_linenum * 1.0 / (change_linenum if change_linenum > 0 else 1), 2)

        env = templates()
        increment_report_tpl = env.get_template('delta_coverage_report.html')
        changed_covered_details = {}
        for filename in changes.keys():
            change_num = len(changes[filename])
            uncov_num = 0
            if uncovers.has_key(filename):
                uncov_num = len(uncovers[filename])
            assert(change_num >= uncov_num)
            changed_covered_details[filename] = (change_num, change_num - uncov_num, changes[filename])
        content = increment_report_tpl.render(
                current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
        cov_lines=cov_linenum,
        change_linenum= change_linenum,
        coverage=coverage * 100,
        from_commit=self.since,
        to_commit=self.until,
        # changed num, covered num, changed details.
        details_trs=self.create_coverage_trs(changed_covered_details))
        open(os.path.join(self.report_dir, 'increment_coverage_report.html'), 'w').write(content)
        pprint("summary of this commit: total line num %d, covered %d, coverage %.2f%%" % (change_linenum, cov_linenum, coverage*100))
        pprint(">>>> create_report")
        return coverage

    def check(self):
        # main function
        src_files = self.get_changed_files()
        changes = self.get_changed_lines(src_files)
        lcov_changes, uncovers = self.get_recoverage_info(changes)
        return 0 if self.create_report(lcov_changes, uncovers) > self.thresh else 1


def run_example():
    monitor, report_dir, threshold = ['["pls"]', "test_output/report/", 0.01]
    input_test_1 = ["7fff..01222", report_dir, "utcov.", "src/", threshold, monitor]
    if DEBUG:
        pprint("input_test_1: ", input_test_1)
    ut = UTCover(*input_test_1)
    src_files = ut.get_changed_files()
    changes = ut.get_changed_lines(src_files)
    lcov_changes, uncovers = ut.get_recoverage_info(changes)
    ut.create_report(changes, uncovers)
    sys.exit(0)


def generate_delta_report(options):
    since_commit = options.since
    until_commit = options.until
    html_dir = options.source_report_dir
    prefix = options.prefix
    missing_prefix_dir = options.missing_prefix_dir
    UTCover(since_commit=since_commit,
            until_commit=until_commit,
            report_dir=html_dir,
            prefix=prefix,
            missing_prefix_dir=missing_prefix_dir,
            thresh=0.2).check()
    sys.exit(0)
