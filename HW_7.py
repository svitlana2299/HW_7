from collections import UserDict
from datetime import date, timedelta
import pickle

# клас Field, містить у собі валідацію та інформацію про значення поля (значення зберігається у змінній _value).


class Field:
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value


class Name(Field):
    pass

# Клас Phone має додатковий метод _validate_phone_number() для перевірки телефонного номеру на коректність.


class Phone(Field):
    def __init__(self, phone):
        super().__init__(phone)
        self._validate_phone_number()

    def _validate_phone_number(self):
        if not self.value.isdigit():
            raise ValueError("Phone number should only contain digits")
        if len(self.value) > 15:
            raise ValueError(
                "Phone number should only contain up to 15 digits")


class Email(Field):
    pass


class Birthday(Field):
    def __init__(self, value=None):
        super().__init__(value)
        self._validate_birthday()

    def _validate_birthday(self):
        if self.value is not None and not isinstance(self.value, date):
            raise ValueError("Birthday should be a date object")

    def days_to_birthday(self):
        if self.value is None:
            return
        current_date = date.today()
        current_year_birthday = self.value.replace(year=current_date.year)
        if current_year_birthday < current_date:
            current_year_birthday = current_year_birthday.replace(
                year=current_date.year + 1)
        delta = current_year_birthday - current_date
        return delta.days


class Record:
    def __init__(self, name, phone=None, email=None, birthday=None):
        self.name = Name(name)
        self.email = Email(email)
        self.birthday = Birthday(birthday)
        self.phones = []
        if phone is not None:
            for ph in phone:
                self.add_phone(ph)

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        for ph in self.phones:
            if ph.value == phone:
                self.phones.remove(ph)
                break

    def edit_phone(self, old_phone, new_phone):
        for ph in self.phones:
            if ph.value == old_phone:
                ph.value = new_phone
                break

    def __str__(self):
        return f"Name: {self.name.value}\nPhones: {', '.join([phone.value for phone in self.phones]) if self.phones else '-'}\nEmail: {self.email.value or '-'}\nBirthday: {self.birthday.value or '-'}"

    def days_to_birthday(self):
        if self.birthday:
            return self.birthday.days_to_birthday()


class AddressBook(UserDict):
    def add_record(self, record):
        if not isinstance(record, Record):
            raise TypeError("Can only add Record objects")
        if record.name.value in self.data:
            raise ValueError(
                f"Record with name {record.name.value} already exists")
        self.data[record.name.value] = record

    def delete_record(self, name):
        del self.data[name]

    def edit_record(self, name, **kwargs):
        record = self.data[name]
        if kwargs.get('name'):
            new_name = kwargs['name']
            if new_name != name:
                self.data[new_name] = self.data.pop(name)
                record.name.value = new_name
        if kwargs.get('phones'):
            phones = kwargs['phones']
            record.phones = [Phone(phone) for phone in phones]
        if kwargs.get('email'):
            email = kwargs['email']
            record.email = Email(email) if email else None
        if kwargs.get('birthday'):
            birthday = kwargs['birthday']
            record.birthday = Birthday(birthday) if birthday else None

    def search_records(self, **kwargs):
        result = []
        for record in self.data.values():
            for key, value in kwargs.items():
                if key == 'name' and value.lower() in record.name.value.lower():
                    result.append(record)
                elif key == 'phone':
                    for phone in record.phones:
                        if phone.value and value in phone.value:
                            result.append(record)
                            break
                        elif phone.value and value.lower() in phone.value.lower():
                            result.append(record)
                            break
                        elif phone.value and value in phone.value.split():
                            result.append(record)
                            break
                        elif phone.value and any(substring in phone.value for substring in value.split()):
                            result.append(record)
                            break
                        elif phone.value and phone.value.find(value) != -1:
                            result.append(record)
                            break
                        elif phone.value and phone.value.find(''.join(value.split())) != -1:
                            result.append(record)
                            break
                elif key == 'email' and record.email and record.email.value and value.lower() in record.email.value.lower():
                    result.append(record)
                elif key == 'birthday' and record.birthday and record.birthday.days_to_birthday() == value:
                    result.append(record)
        return result

    def iterator(self, page_size):
        return AddressBookIterator(self.data, page_size)

    def save_to_file(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.data, file)

    @classmethod
    def load_from_file(cls, filename):
        with open(filename, 'rb') as file:
            data = pickle.load(file)
            address_book = cls()
            address_book.data = data
            return address_book

# Клас AddressBookIterator є ітератором для адресної книги, який реалізує пагінацію - розбиття на сторінки з певною кількістю записів. При створенні ітератора передається адресна книга та розмір сторінки, а далі можна ітеруватися по сторінках та записам.


class AddressBookIterator:
    def __init__(self, address_book, page_size):
        if page_size <= 0:
            raise ValueError('Page size should be greater than zero.')
        self._address_book = address_book
        self._page_size = page_size
        self._current_page = 0
        self._current_record = 0
        self._records = list(address_book.values())

    def __iter__(self):
        return self

    def __next__(self):
        if self._current_page >= len(self._records) // self._page_size:
            raise StopIteration

        start = self._current_page * self._page_size
        end = start + self._page_size
        page = self._records[start:end]

        if self._current_record >= len(page):
            self._current_page += 1
            self._current_record = 0
            return self.__next__()

        record = page[self._current_record]
        self._current_record += 1
        return record

    def __str__(self):
        return "\n".join([f"{record.name.value}: {record.phones}, {record.email}, {record.birthday}" for record in self.data.values()])


