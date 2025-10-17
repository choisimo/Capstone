import React, { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { FileText, Bold, Italic, Underline, Strikethrough, List, ListOrdered, Link as LinkIcon, Undo2, Redo2, Type, X, Download } from "lucide-react";

// Lightweight rich text editor using contentEditable with a toolbar.
// Persists to localStorage, draggable, and resizable.

const STORAGE_KEY = "memo_pad_content_v1";
const STORAGE_POS_KEY = "memo_pad_pos_v1";
const STORAGE_OPEN_KEY = "memo_pad_open_v1";

export default function MemoPad() {
  const [open, setOpen] = useState<boolean>(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_OPEN_KEY) || "false"); } catch { return false; }
  });
  const [position, setPosition] = useState<{x:number;y:number}>(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE_POS_KEY) || "{\"x\":0,\"y\":0}"); } catch { return { x: 0, y: 0 }; }
  });
  const [dragging, setDragging] = useState(false);
  const [offset, setOffset] = useState<{x:number;y:number}>({ x: 0, y: 0 });
  const editorRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (editorRef.current) {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) editorRef.current.innerHTML = saved;
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_OPEN_KEY, JSON.stringify(open));
  }, [open]);

  useEffect(() => {
    localStorage.setItem(STORAGE_POS_KEY, JSON.stringify(position));
  }, [position]);

  const exec = (command: string, value?: string) => {
    document.execCommand(command, false, value);
    // persist after command
    save();
  };

  const makeLink = () => {
    const url = prompt("링크 URL을 입력하세요");
    if (!url) return;
    exec("createLink", url);
  };

  const save = () => {
    const html = editorRef.current?.innerHTML || "";
    localStorage.setItem(STORAGE_KEY, html);
  };

  const clear = () => {
    if (editorRef.current) {
      editorRef.current.innerHTML = "";
      save();
    }
  };

  const downloadHTML = () => {
    const blob = new Blob([editorRef.current?.innerHTML || ""], { type: "text/html;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "memo.html";
    a.click();
  };

  // Drag handlers
  const onMouseDown = (e: React.MouseEvent) => {
    setDragging(true);
    setOffset({ x: e.clientX - position.x, y: e.clientY - position.y });
  };
  const onMouseMove = (e: MouseEvent) => {
    if (!dragging) return;
    setPosition({ x: Math.max(8, e.clientX - offset.x), y: Math.max(8, e.clientY - offset.y) });
  };
  const onMouseUp = () => setDragging(false);

  useEffect(() => {
    if (!open) return;
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [open, dragging, offset]);

  return (
    <div>
      {/* Floating toggle button */}
      <div className="fixed bottom-6 right-6 z-[60]">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button onClick={() => setOpen((v) => !v)} size="sm" className="h-10 shadow-lg">
                <FileText className="h-4 w-4 mr-2" /> 메모
              </Button>
            </TooltipTrigger>
            <TooltipContent>떠다니는 메모장 열기/닫기</TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Floating memo panel */}
      {open && (
        <div
          className={cn(
            "fixed z-[61] w-[min(560px,95vw)] select-none",
          )}
          style={{ left: position.x || 16, top: position.y || 80 }}
        >
          <Card className="shadow-elevated border-border/60 backdrop-blur supports-[backdrop-filter]:bg-background/80">
            <CardHeader className="py-3 cursor-move active:cursor-grabbing" onMouseDown={onMouseDown}>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium">빠른 메모</CardTitle>
                <div className="flex items-center gap-1">
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={downloadHTML} title="HTML로 저장">
                    <Download className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setOpen(false)} title="닫기">
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              {/* Toolbar */}
              <div className="flex flex-wrap items-center gap-1 p-2 rounded-md border border-border/60 bg-muted/40">
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => exec("bold") } title="굵게">
                  <Bold className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => exec("italic") } title="기울임">
                  <Italic className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => exec("underline") } title="밑줄">
                  <Underline className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => exec("strikeThrough") } title="취소선">
                  <Strikethrough className="h-4 w-4" />
                </Button>
                <span className="w-px h-6 bg-border mx-1" />
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8">
                      <Type className="h-4 w-4 mr-1" /> 스타일
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-44 p-1">
                    <div className="flex flex-col">
                      <Button variant="ghost" className="justify-start" onClick={() => exec("formatBlock", "<p>")}>본문</Button>
                      <Button variant="ghost" className="justify-start" onClick={() => exec("formatBlock", "<h1>")}>제목 1</Button>
                      <Button variant="ghost" className="justify-start" onClick={() => exec("formatBlock", "<h2>")}>제목 2</Button>
                      <Button variant="ghost" className="justify-start" onClick={() => exec("formatBlock", "<h3>")}>제목 3</Button>
                      <Button variant="ghost" className="justify-start" onClick={() => exec("removeFormat")}>서식 제거</Button>
                    </div>
                  </PopoverContent>
                </Popover>
                <span className="w-px h-6 bg-border mx-1" />
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => exec("insertUnorderedList") } title="글머리 기호">
                  <List className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => exec("insertOrderedList") } title="번호 매기기">
                  <ListOrdered className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={makeLink} title="링크 삽입">
                  <LinkIcon className="h-4 w-4" />
                </Button>
                <span className="w-px h-6 bg-border mx-1" />
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => exec("undo") } title="실행 취소">
                  <Undo2 className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => exec("redo") } title="다시 실행">
                  <Redo2 className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="sm" className="h-8 ml-auto" onClick={clear}>비우기</Button>
              </div>

              {/* Editor */}
              <div
                ref={editorRef}
                contentEditable
                onInput={save}
                className="mt-2 min-h-[200px] max-h-[60vh] overflow-auto rounded-md border border-border bg-background p-3 text-sm leading-6 shadow-sm focus:outline-none"
                style={{ resize: "vertical" as const }}
                placeholder="메모를 입력하세요..."
                suppressContentEditableWarning
              />
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
