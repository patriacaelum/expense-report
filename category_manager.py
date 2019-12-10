import json
import logging

from difflib import get_close_matches


logger = logging.getLogger(__name__)


class CategoryManager:
    """A JSON based manager for categories.

    This class is meant to handle all file reading and writing regarding the
    categories, and for querying and adding categories as needed.

    The data is at most two levels deep, enough for a category and a
    subcategory. The data is split into cats, which maps subcategories to their
    respective categories, and subcats, which maps expenses to their respective
    subcategories.

    filename: (str) the name of the JSON file that stores the categories.
    """
    def __init__(self, filename='cats.json'):
        self.filename = filename

        try:
            logger.debug(f'Loading category data from {self.filename}')

            with open(self.filename, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            logger.warning(f'{self.filename} not found, using empty data set')
            data = dict()

        logger.debug('Sorting data into categories and subcategories')

        self.cats = dict()
        self.subcats = dict()
        for cat, catval in data.items():
            for subcat, subval in catval.items():
                self.cats[subcat] = cat

                for expense in subval:
                    self.subcats[expense] = subcat

        logger.info('Successfully sorted data into categories and subcategories')

    def write(self):
        """Writes JSON data to the file.

        No file is created if there is no data.

        The data is reformatted into a hierarchial tree.
        """
        data = dict()

        logger.debug('Sorting categories and subcategories into hierarchial tree')

        for expense, subcat in self.subcats.items():
            if subcat not in data.keys():
                data[subcat] = [expense]
            else:
                data[subcat].append(expense)

        for subcat, cat in self.cats.items():
            if cat not in data.keys():
                data[cat] = dict()

            data[cat].update({subcat: data[subcat]})
            del data[subcat]

        logger.info('Successfully sorted categories and subcategories into a hierarchial tree')


        if len(self.cats) != 0:
            logger.info(f'Writing data to {self.filename}')

            with open(self.filename, 'w') as file:
                json.dump(data, file)

    def query(self, query):
        """Looks for the category and subcategory of the queried expense.

        If it doesn't exist, then the user will be asked to provide one.

        query: (str) the expense.
        """
        query = query

        subcat = self.subcats.get(query)
        cat = self.cats.get(subcat)

        if cat is None or subcat is None:
            matches = get_close_matches(query, self.subcats.keys())

            if len(matches) == 0:
                print(f'\nNo matches for "{query}", adding a new category')
                cat, subcat = self._add_query(query)
            else:
                print(f'\nNo matches for "{query}", did you mean one of these?')

                for i in range(len(matches)):
                    print(f'{i+1}) {matches[i]}')

                print(f'{i+2}) None of the above')

                choice = int(input(f'\n[1-{i+2}]: '))

                if choice == len(matches) + 1:
                    cat, subcat = self._add_query(query)
                else:
                    query = matches[choice - 1]
                    subcat = self.subcats.get(query)
                    cat = self.cats.get(subcat)

        return cat, subcat, query

    def _add_query(self, query):
        """Updates the currently stored categories and subcategories.

        query: (str) the expense.
        """
        # Determine category
        cats = list(sorted(set(self.cats.values())))
        cat = self._get_input(query, 'category', cats)

        # Determine subcategory
        subcats = list(sorted(
            [key for key, value in self.cats.items() if value == cat]
        ))
        subcat = self._get_input(query, 'subcategory', subcats)

        # Update categories
        logger.debug('Updating categories and subcategories')

        if cat not in cats:
            self.cats[subcat] = cat

        if subcat not in subcats:
            self.cats[subcat] = cat

        self.subcats[query] = subcat

        return cat, subcat

    def _get_input(self, query, ntype, choices=list()):
        """Asks the user to provide a category and subcategory for the expense.

        It will ask to choose from a list of existing choices or to provide a
        new one entirely.

        query:   (str) the expense.
        ntype:   (str) what we're asking for, i.e. "category" or "subcategory".
        choices: (list) the existing possibilities.
        """
        valid = False
        nchoices = len(choices)

        while not valid:
            if nchoices == 0:
                choice = input(
                    f'\nPlease specify a {ntype} for "{query}": '
                ).lower()

                if choice not in set(self.cats.values()) and choice not in self.cats.keys():
                    valid = True
                else:
                    print(f'\n{choice} is invalid because it already exists')

            else:
                print(f'\nPlease choose an {ntype} for "{query}":')
                for i in range(nchoices):
                    print(f'{i+1}) {choices[i]}')

                print(f'{i+2}) None of the above')

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
                    choice = choices[choice - 1]
                    valid = True
                else:
                    print(f'\n{choice} is an invalid choice')

        return choice

