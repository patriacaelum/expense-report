import logging
import subprocess


logger = logging.getLogger(__name__)


class TexGenerator:
    """A class that formats and creates a basic template for a LaTeX document.

    filename: (str) the filename of the LaTeX document.
    """
    def __init__(self, filename):
        self.filename = filename
        self.text = ""

    def add_header(self):
        logger.debug('Adding header')

        self.text += r"""
\documentclass[12pt, onecolumn, twoside]{article}

\usepackage[paperwidth=215.9mm, paperheight=279mm, hmargin=2.5cm, vmargin=2.5cm, centering]{geometry}
\usepackage{graphicx}
\usepackage{lettrine}
\usepackage{multirow}
\usepackage{scrextend}
\usepackage{siunitx}


\begin{document}

"""

    def add_title(self, title):
        logger.debug('Adding title')

        self.text += f"""
\\title{{{title}}}
\\date{{}}
\\maketitle
\\newpage


\\tableofcontents
\\newpage

"""

    def add_section(self, section):
        logger.debug('Adding section')

        self.text += f'\n\\section{{section}}'

    def add_figure(self, filename):
        logger.debug(f'Adding a figure from {filename}')

        self.text += f"""
\\begin{{figure}}[ht]
  \\centering
  \\includegraphics[width=\\textwidth]{{{filename}}}
\\end{{figure}}

"""

    def add_table(self, data, total):
        logger.debug('Adding data to a table')

        # Open table and create column names
        self.text += r"""
\begin{table}[ht]
  \centering
  \begin{tabular}{llllr}
    Date & Category & Subcategory & Expense & Price (\$) \\ \hline \hline
    """

        # Create table rows
        rows = ['' for _ in range(self._nitems(data))]
        rows = self._generate_table(data, rows)
        self.text += '\n    '.join(rows)

        # Add final row for total expenses
        self.text += f' \\hline \\hline\n    \multicolumn{{4}}{{c}}{{TOTAL}} & {total:.2f}'

        # Close table
        self.text += r"""
  \end{tabular}
\end{table}
"""

    def add_footer(self):
        logger.debug('Adding footer')

        self.text += '\n\\end{document}'

    def write(self):
        logger.info(f'Writing tex document to "{self.filename}"')
        with open(self.filename, 'w') as file:
            file.write(self.text)

    def compile(self):
        pdflatex = subprocess.run(['pdflatex', self.filename])

        if pdflatex.returncode == 0:
            logger.info('Successfully compiled LaTeX document')
        else:
            logger.error('Failed to compile LaTeX document')

        prefix = self.filename[:-4]
        rmrf = subprocess.run([
            'rm',
            '-rf',
            prefix + '.aux',
            prefix + '.log',
            prefix + '.tex',
            prefix + '.toc'
        ])

        if rmrf.returncode == 0:
            logger.info('Successfully removed residual files')
        else:
            logger.error('Failed to remove residual files')

    def _generate_table(self, data, rows, r=0, c=1):
        """Recursively creates a table using multirows.

        This method only writes the contents of the table, and does not
        initialize it nor closes it.

        data: (dict) the data can either be a nested dictionary, in which case
              this function is called again recursively, or a simple dictionary,
              in which case the key and value are assumed to be the expense and
              price.
        rows: (list) a list of strings representing each row of the table. When
              initally calling this method, this should be a list of empty
              strings.
        r:    (int) the current row. This does not need to be specified for the
              initial call.
        c:    (int) the current column. This does not need to be specified for
              the initial call.

        returns: (list) the updated rows of strings.
        """
        i = 0
        for key, value in data.items():
            if isinstance(value, dict):
                # Nested dictionaries are assumed to be multirows
                n = self._nitems(value)

                rows[r + i] += f'\\multirow{{{n}}}{{*}}{{{key.title()}}} '

                for j in range(n):
                    rows[r + i + j] += '& '

                rows = self._generate_table(value, rows, r + i, c + 1)

                # Retroactively fix column line
                rows[r + i + n - 1] = rows[r + i + n - 1][:-5] + f'{{{c}-5}}'

                i += n
            else:
                # Last columns are assumed to be expense and price
                rows[r + i] += f'{key.title()} & {value:.2f} \\\\ \\cline{{{c}-5}}'

                i += 1

        return rows

    def _nitems(self, data):
        """Recursively counts the number of items in a nested dictionary.

        data: (dict) a nested dictionary.

        returns: (int) the number of items in the data.
        """
        n = 0
        for key, value in data.items():
            if isinstance(value, dict):
                n += self._nitems(value)
            else:
                n += 1

        return n

