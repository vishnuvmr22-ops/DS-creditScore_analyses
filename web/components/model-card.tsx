"use client";

import { Fragment, type ReactNode } from "react";

/**
 * The generated model card, rendered readable and verbatim (FR-007).
 *
 * A deliberately small renderer for the subset the card actually uses —
 * headings, lists, tables, emphasis and code. Nothing is summarised, reordered
 * or dropped: a governance document that the viewer edits is not the document.
 */

const INLINE = /(\*\*[^*]+\*\*|_[^_]+_|`[^`]+`)/g;

function renderInline(text: string): ReactNode[] {
  return text.split(INLINE).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("_") && part.endsWith("_") && part.length > 2) {
      return <em key={index}>{part.slice(1, -1)}</em>;
    }
    if (part.startsWith("`") && part.endsWith("`") && part.length > 2) {
      return (
        <code key={index} className="num bg-[var(--color-sunk)] px-1 text-[0.9em]">
          {part.slice(1, -1)}
        </code>
      );
    }
    return <Fragment key={index}>{part}</Fragment>;
  });
}

function splitRow(line: string): string[] {
  return line
    .trim()
    .replace(/^\||\|$/g, "")
    .split("|")
    .map((cell) => cell.trim());
}

const isTableRow = (line: string) => line.trim().startsWith("|");
const isTableRule = (line: string) => /^\|[\s:|-]+\|$/.test(line.trim());

export function ModelCardView({ content }: { content: string }) {
  const lines = content.split("\n");
  const blocks: ReactNode[] = [];
  let paragraph: string[] = [];
  let list: string[] = [];

  const flushParagraph = () => {
    if (paragraph.length === 0) return;
    blocks.push(
      <p key={`p${blocks.length}`} className="max-w-prose text-[13px] leading-relaxed">
        {renderInline(paragraph.join(" "))}
      </p>,
    );
    paragraph = [];
  };

  const flushList = () => {
    if (list.length === 0) return;
    blocks.push(
      <ul key={`u${blocks.length}`} className="max-w-prose list-disc space-y-1 pl-5 text-[13px]">
        {list.map((item, index) => (
          <li key={index}>{renderInline(item)}</li>
        ))}
      </ul>,
    );
    list = [];
  };

  const flushAll = () => {
    flushParagraph();
    flushList();
  };

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const trimmed = line.trim();

    if (trimmed.length === 0) {
      flushAll();
      continue;
    }

    if (isTableRow(trimmed)) {
      flushAll();
      const rows: string[][] = [];
      while (index < lines.length && isTableRow(lines[index])) {
        if (!isTableRule(lines[index])) rows.push(splitRow(lines[index]));
        index += 1;
      }
      index -= 1;
      const [head, ...body] = rows;
      blocks.push(
        <div key={`t${blocks.length}`} className="scroll-x">
          <table className="ledger max-w-prose">
            <thead>
              <tr>
                {head.map((cell) => (
                  <th key={cell} className="label label-ink">
                    {cell}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {body.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className={cellIndex > 0 ? "num" : undefined}>
                      {renderInline(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }

    const heading = /^(#{1,4})\s+(.*)$/.exec(trimmed);
    if (heading) {
      flushAll();
      const level = heading[1].length;
      const size = level === 1 ? "text-[17px]" : level === 2 ? "text-[14px]" : "text-[13px]";
      blocks.push(
        <p
          key={`h${blocks.length}`}
          className={`${size} mt-5 font-semibold tracking-tight first:mt-0`}
        >
          {renderInline(heading[2])}
        </p>,
      );
      continue;
    }

    if (/^[-*]\s+/.test(trimmed)) {
      flushParagraph();
      list.push(trimmed.replace(/^[-*]\s+/, ""));
      continue;
    }

    flushList();
    paragraph.push(trimmed);
  }

  flushAll();

  return <div className="space-y-3 px-4 py-4">{blocks}</div>;
}
