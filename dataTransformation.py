import re
from abc import ABC


class DataTransformerInterface(ABC):
    def transform(self, data: str) -> str: ...


class NoTransform(DataTransformerInterface):
    def transform(self, data: str) -> str:
        return data


class SleepSessionTimeDataTransform(DataTransformerInterface):
    _pattern = re.compile(r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?$")

    def transform(self, data: str) -> str:
        """
        Преобразует строки вида 'PT1H10M', 'PT2H', 'PT45M' в общее число минут.
        Другие строки возвращает без изменений.
        """
        match = self._pattern.match(data)
        if data.isdigit():
            return str(data)

        if match:
            hours = int(match.group("hours") or 0)
            minutes = int(match.group("minutes") or 0)
            return str(hours * 60 + minutes)

        raise ValueError(f"Invalid duration format: {data!r}")


data_transformer_by_datatype = {"SleepSessionTimeData": SleepSessionTimeDataTransform()}

no_transform = NoTransform()


def get_data_transformer_by_datatype(datatype: str):
    return data_transformer_by_datatype.get(datatype, no_transform)
