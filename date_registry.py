from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional

class DateRegistry:
    """
    Registry for date-versioned objects.
    Each object becomes active from its start date until overridden by a newer one.
    Supports callable or non-callable objects.
    """

    def __init__(self):
        self._registry: Dict[str, List[Tuple[datetime, Any]]] = {}
        self._default_objs: Dict[str, Any] = {}

    def register(self, name: str, start: str, obj: Any):
        """
        Registers an object starting from a specific date for a given name.

        Args:
            name: Identifier for the group/module.
            start: Start date in 'YYYY-MM-DD' format. If None defaults to "1970-01-01"
            obj: The object to register (can be anything).
        """
        if(start_dt is None):
            start_dt = "1970-01-01"
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        self._registry.setdefault(name, []).append((start_dt, obj))
        self._registry[name].sort(reverse=True)

    def set_default(self, name: str, obj: Any):
        """
        Sets a default object to use if no start date applies.

        Args:
            name: Identifier for the group/module.
            obj: Default fallback object.
        """
        self._default_objs[name] = obj

    def get(self, name: str, target_date: str) -> Optional[Any]:
        """
        Retrieves the object appropriate for the target date.

        Args:
            name: Identifier for the group/module.
            target_date: The target date in 'YYYY-MM-DD' format.

        Returns:
            The registered object for the target date, or the default if none match.
        """
        date = datetime.strptime(target_date, "%Y-%m-%d")
        for start_dt, obj in self._registry.get(name, []):
            if date >= start_dt:
                return obj
        return self._default_objs.get(name)

    def run(self, name: str, target_date: str, *args, **kwargs):
        """
        Gets the object for the given date and, if callable, runs it with args.
        Otherwise, returns the object itself.

        Args:
            name: Identifier of the group/module.
            target_date: Date string in 'YYYY-MM-DD' format.
            *args: Arguments to pass to the object if it's callable.
            **kwargs: Keyword arguments to pass to the object if callable.

        Returns:
            Result of calling the object or the object itself.

        Raises:
            ValueError: If no matching object is found.
        """
        obj = self.get(name, target_date)
        if obj is None:
            raise ValueError(f"No object registered for '{name}' on date {target_date}")
        return obj(*args, **kwargs) if callable(obj) else obj


if __name__ == "__main__":
    registry = DateRegistry()

    # Different versions of the parser function
    def parse_v1(text):
        return f"[v1 parse] {text}"

    def parse_v2(text):
        return f"[v2 parse] {text.upper()}"

    # File header formats over time
    headers_v1 = ["id", "name", "age"]
    headers_v2 = ["uuid", "full_name", "age", "email"]

    # Registering by role name
    registry.register("parse_fn", "2000-01-01", parse_v1)
    registry.register("parse_fn", "2020-01-01", parse_v2)

    registry.register("file_headers", "2000-01-01", headers_v1)
    registry.register("file_headers", "2022-01-01", headers_v2)

    # Use cases
    print(registry.run("parse_fn", "2010-05-01", "John Doe"))      # v1 parser
    print(registry.run("parse_fn", "2023-03-12", "Jane Smith"))    # v2 parser
    print(registry.get("file_headers", "2015-06-01"))              # headers_v1
    print(registry.get("file_headers", "2023-06-01"))              # headers_v2