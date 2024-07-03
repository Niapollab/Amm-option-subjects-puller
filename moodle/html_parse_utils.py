from collections import deque
from dataclasses import dataclass
from moodle.exceptions import CorruptedHtmlError
from typing import Iterable, Mapping
import re


@dataclass(frozen=True)
class HtmlTag:
    """Represents an HTML tag with its attributes and inner text."""

    name: str
    """The name of the HTML tag (e.g., 'div', 'span')."""

    attributes: Mapping[str, str]
    """A dictionary of the tag's attributes and their values."""

    inner_text: str | None
    """The inner text contained within the HTML tag, if any."""

    def enumerate_tag_by_name(self, name: str) -> Iterable["HtmlTag"]:
        """Enumerates HTML tags by name and yields HtmlTag objects.

        Args:
            name (str): The name of the HTML tag to search for.

        Yields:
            HtmlTag: An HtmlTag object representing a found tag with its attributes and inner text.

        Raises:
            CorruptedHtmlError: If an unpaired open or close tag is found.
        """

        return enumerate_tag_by_name(self.inner_text or "", name)


def enumerate_tag_by_name(html: str, name: str) -> Iterable[HtmlTag]:
    """Enumerates HTML tags by name and yields HtmlTag objects.

    Args:
        html (str): The HTML content as a string.
        name (str): The name of the HTML tag to search for.

    Yields:
        HtmlTag: An HtmlTag object representing a found tag with its attributes and inner text.

    Raises:
        CorruptedHtmlError: If an unpaired open or close tag is found.
    """

    TAG_PATTERN = re.compile(rf"(?:<\/{name}>)|(?:<{name}(.*?)(\/)?>)", re.S)
    tag_stack = deque()

    for tag in TAG_PATTERN.finditer(html):
        is_close_tag = tag[1] is None
        is_one_liner = tag[2] is not None

        if is_close_tag:
            if not tag_stack:
                raise CorruptedHtmlError(
                    f'Found unpaired close tag in position "{tag.pos}".'
                )

            head_pos, head_len, attributes = tag_stack.pop()
            head_end_pos = head_pos + head_len

            tail_start_pos = tag.regs[0][0]
            inner_text = html[head_end_pos:tail_start_pos]

            yield HtmlTag(name, attributes, inner_text)
            continue

        attributes = __parse_tag_attributes(tag[1])

        if is_one_liner:
            yield HtmlTag(name, attributes, None)
            continue

        tag_stack.append((tag.regs[0][0], len(tag[0]), attributes))

    if tag_stack:
        tag_pos, *_ = tag_stack[0]
        raise CorruptedHtmlError(f'Found unpaired open tag in position "{tag_pos}".')


def __parse_tag_attributes(raw_attributes: str) -> Mapping[str, str]:
    ATTRIBUTE_PATTERN = re.compile(r'([^\s]*?)="(.*?)"', re.S)
    return {m[1]: m[2] for m in ATTRIBUTE_PATTERN.finditer(raw_attributes)}
