import logging
import matplotlib.pyplot as plt
import subprocess

from category_manager import CategoryManager
from collections import namedtuple
from csv import DictReader
from tex_generator import TexGenerator


logger = logging.getLogger(__name__)


class ExpenseReport:
    """Generates the expense report.

    xfile:   (str) the CSV file containing the expenses.
    catfile: (str) the JSON file of the categories.
    """
    def __init__(self, xfile, catfile='cats.json'):
        self.filename = xfile

        self.catman = CategoryManager(catfile)

        self.expenses = list()
        self.figures = list()

    def generate_report(self):
        self._categorize_expenses()
        self._generate_graphs()
        self._generate_pdf()
        self._clean_graphs()

    def _categorize_expenses(self):
        logger.debug(f'Categorizing expenses from {self.filename}')

        Expense = namedtuple(
            'Expense',
            ['date', 'cat', 'subcat', 'expense', 'price']
        )

        date = ""
        with open(self.filename, 'r') as file:
            reader = DictReader(file)

            for row in reader:
                expense = row['Expense'].lower()
                price = float(row['Price'])

                # Reuse older date if not specified
                if row['Date'].strip() != "":
                    date = row['Date']

                query = self.catman.query(expense)

                if query is None:
                    self.catman.add(expense, price)
                    query = self.catman.query(expense)
                else:
                    self.catman.update(expense, price)

                self.expenses.append(Expense(
                    date=date,
                    cat=query['cat'],
                    subcat=query['subcat'],
                    expense=expense,
                    price=price
                ))

        logger.info(f'Successfully categorized expenses from {self.filename}')

    def _generate_graphs(self):
        logger.debug('Creating pie charts for overall and categorical expenses')

        # Organize data for pie charts
        overall = dict()
        category = dict()

        for x in self.expenses:
            # Add expense to overall categories
            if x.cat not in overall.keys():
                overall[x.cat] = 0

            overall[x.cat] += x.price

            # Add expense to subcategories
            if x.cat not in category.keys():
                category[x.cat] = dict()

            if x.subcat not in category[x.cat].keys():
                category[x.cat][x.subcat] = 0

            category[x.cat][x.subcat] += x.price

        overall = {'overall': overall}

        self._generate_pie_chart(overall)
        self._generate_pie_chart(category)

        logger.info('Successfully created all pie charts')

    def _generate_pie_chart(self, data):
        def pformat(pct, total):
            value = pct / 100.0 * total
            return f'${value:.2f}\n({pct:.0f}%)'

        if len(data) == 1:
            logger.debug('Creating single pie chart')

            # Clear previous plot
            plt.clf()
            plt.cla()

            fig, ax = plt.subplots(nrows=1, ncols=1, dpi=300, figsize=(6, 6))

            for title, cats in data.items():
                # Create pie chart
                ax.pie(
                    cats.values(),
                    labels=cats.keys(),
                    autopct=lambda x: pformat(x, sum(cats.values()))
                )
                ax.set(title=f'{title.title()} Expenses')

                # Keep track of created figures
                filename = f'{title.replace(" ", "_")}.png'
                plt.savefig(filename)
                self.figures.append(filename)
        else:
            logger.debug('Creating sheet of pie charts')

            # Clear previous plot
            plt.clf()
            plt.cla()
            fig, ax = plt.subplots(nrows=3, ncols=2, dpi=300, figsize=(6, 9))
            for indx, (cat, subcats) in enumerate(data.items()):
                row = (indx % 6) // 2
                col = indx % 2

                # Create pie chart
                ax[row, col].pie(
                    subcats.values(),
                    labels=subcats.keys(),
                    autopct=lambda x: pformat(x, sum(subcats.values()))
                )
                ax[row, col].set(title=f'{cat.title()} Expenses')

                # Make new plot if all six figures are filled
                if indx % 6 == 5:
                    logger.warning('All six pie charts are filled, creating a new sheet')

                    # Keep track of created figures
                    filename = f'category{indx // 6}.png'
                    plt.savefig(filename)
                    self.figures.append(filename)

                    # Clear previous plot
                    plt.clf()
                    plt.cla()

                    fig, ax = plt.subplots(nrows=2, ncols=3, dpi=300)
            else:
                logger.warning('Clearing empty pie charts')

                # Clear empty plots
                for i in range(indx + 1, (indx // 6 + 1) * 6):
                    row = (i % 6) // 2
                    col = i % 2

                    ax[row, col].axis('off')

                # Save the last figure
                filename = f'category{indx // 6}.png'
                plt.savefig(filename)
                self.figures.append(filename)

    def _generate_pdf(self):
        texgen = TexGenerator(self.filename[:-4] + '.tex')
        texgen.add_header()
        texgen.add_title(self.filename[:-4].replace('_', ' ').title())

        texgen.add_section('Expense Charts')

        for filename in self.figures:
            texgen.add_figure(filename)

        texgen.add_section('Expense Data')

        # Reorganize data with date first
        total = 0
        data = dict()
        for x in self.expenses:
            if x.date not in data.keys():
                data[x.date] = dict()

            if x.cat not in data[x.date].keys():
                data[x.date][x.cat] = dict()

            if x.subcat not in data[x.date][x.cat].keys():
                data[x.date][x.cat][x.subcat] = dict()

            if x.expense not in data[x.date][x.cat][x.subcat].keys():
                data[x.date][x.cat][x.subcat][x.expense] = 0

            data[x.date][x.cat][x.subcat][x.expense] += x.price
            total += x.price

        texgen.add_table(data, total)

        texgen.add_footer()

        texgen.write()
        texgen.compile()

    def _clean_graphs(self):
        logger.debug('Removing created graphs')

        for filename in self.figures:
            rmrf = subprocess.run(['rm', '-rf', filename])

        if rmrf.returncode == 0:
            logger.info('Successfully removed graphs')
        else:
            logger.error('Failed to remove graphs')

        self.figures = list()

