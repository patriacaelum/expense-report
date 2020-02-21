import json
import logging

from difflib import get_close_matches


logger = logging.getLogger(__name__)


class CategoryManager:
    """A json-based manager for categories.

    This class is meant to handle all file reading and writing regarding the
    categories, and for querying and adding categories as needed.

    The data is stored in a dictionary with the structure

    {
        expense: {
            'cat': category,
            'subcat': subcategory,
            'mean': average price,
            'npurchases': number of purchases,
        }
    }

    filename: (str) the name of the file that stores the categories.
    """
    def __init__(self, filename='cats.json'):
        self.filename = filename

        try:
            logger.info(f'Loading data from {self.filename}')
            with open(self.filename, 'r') as file:
                self.expenses = json.load(file)
        except FileNotFoundError:
            logger.warn(
                f'{self.filename} could not be found, creating empty data set'
            )
            self.expenses = dict()

        logger.debug('Creating quick lookup table for categories')

        self.cats = dict()
        for value in self.expenses.values():
            cat = value['cat']
            subcat = value['subcat']

            if self.cats.get(cat) is None:
                self.cats[cat] = [subcat,]
            elif subcat not in self.cats[cat]:
                self.cats[cat].append(subcat)

        print(self.cats)

    def __del__(self):
        with open(self.filename, 'w') as file:
            json.dump(self.expenses, file)

    def add(self, expense, price):
        """Adds an expense to the currently stored categories and subcategories.

        expense: (str)   the expense.
        price:   (float) the price of expense.
        """
        print(f'\nCreating new expense "{expense}"')

        # Determine category
        cats = list(sorted(self.cats.keys()))
        cat = self._get_input(expense, 'category', cats)

        # Determine subcategory
        subcats = list(sorted(self.cats.get(cat, list())))
        subcat = self._get_input(expense, 'subcategory', subcats)

        # Update categories
        logger.debug('Updating categories and subcategories')

        self.expenses[expense] = {
            'cat': cat,
            'subcat': subcat,
            'mean': price,
            'npurchases': 1,
        }

        if cat not in self.cats.keys():
            self.cats[cat] = list()

        if subcat not in self.cats[cat]:
            self.cats[cat].append(subcat)

    def query(self, expense):
        """Looks for category information of the queried expense.

        If it doesn't exist, then the user will be asked to provide the
        information.

        expense: (str)   the expense.

        return: (dict) the category information of the expense, `None` if the
                       expense does not exist.
        """
        expense = expense.lower()
        query = self.expenses.get(expense)

        if query is None:
            logger.debug('No exact match for "{expense}", look for typo')

            matches = get_close_matches(expense, self.expenses.keys())
            nmatches = len(matches)

            if nmatches > 0:
                print(f'\nNo matches for "{expense}", did you mean:')

                for i in range(nmatches):
                    print(f'{i+1}) {matches[i]}')

                print(f'{nmatches+1}) None of the above')

                valid = False
                while not valid:
                    choice = input(f'\n[1-{nmatches+1}]: ')

                    try:
                        choice = int(choice)
                    except:
                        print(f'\n{choice} is invalid')
                        continue

                    if 1 <= choice <=nmatches + 1:
                        valid = True
                    else:
                        print(f'\n{choice} is invalid')

                if choice != nmatches + 1:
                    query = self.expenses.get(f'{matches[choice-1]}')

        return query

    def update(self, expense, price):
        """Updates the category information of the expense.

        The mean price and number of purchases is updated for the expense.

        expense: (str)   the expense.
        price:   (float) the price of the expense.
        """
        m = self.expenses[expense]['mean']
        N = self.expenses[expense]['npurchases']

        self.expenses[expense]['mean'] = (N * m + price) / (N + 1)
        self.expenses[expense]['npurchases'] = N + 1

    def _get_input(self, expense, ntype, choices=list()):
        """Asks the user to provide a category and subcategory for the expense.

        It will ask to choose from a list of existing choices or to provide a
        new one entirely.

        expense: (str)  the expense.
        ntype:   (str)  what we're asking for, i.e. "category" or "subcategory".
        choices: (list) the existing possibilities.

        return: (str) the category or subcategory from the user.
        """
        valid = False
        nchoices = len(choices)

        while not valid:
            if nchoices == 0:
                choice = input(
                    f'\nPlease specify a {ntype} for "{expense}": '
                ).lower()

                names = set()
                for cat, subcats in self.cats.items():
                    names.add(cat)

                    for subcat in subcats:
                        names.add(subcat)

                if choice not in names:
                    valid = True
                else:
                    print(f'\n{choice} is invalid because it already exists')

            else:
                print(f'\nPlease choose an {ntype} for "{expense}":')
                for i in range(nchoices):
                    print(f'{i+1}) {choices[i]}')

                print(f'{nchoices+1}) None of the above')

                choice = input(f'\n[1-{nchoices+1}]: ')

                try:
                    choice = int(choice)
                except ValueError:
                    print(f'\n{choice} is an invalid choice')
                    continue

                if choice == nchoices + 1:
                    nchoices = 0
                    continue
                elif 1 <= choice <= nchoices:
                    choice = choices[choice-1]
                    valid = True
                else:
                    print(f'\n{choice} is an invalid choice')

        return choice

