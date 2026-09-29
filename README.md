# ai-work-board

Local-first Kanban for humans and AI agents. Markdown tasks + HTML board + tiny CLI.

- แหล่งจริงอยู่ที่ `work-items/` — หนึ่งงาน = หนึ่งไฟล์ Markdown
- โฟลเดอร์ย่อยคือสถานะ: `queued/ running/ review/ done/`
- คนดูหน้า `app/index.html`
- เอเจนต์อัปเดตผ่าน `cli/task.py` หรือแก้ไฟล์ Markdown ได้ตรง ๆ

## เริ่มใช้งาน

```bash
python3 cli/task.py serve          # เปิดบอร์ดที่ http://localhost:8777
```

## CLI

```bash
python3 cli/task.py ls
python3 cli/task.py add "ชื่องาน" --agent Grok --type agent --prio normal
python3 cli/task.py start <id>
python3 cli/task.py log <id> "สรุปสั้น"
python3 cli/task.py progress <id> 40
python3 cli/task.py review <id>
python3 cli/task.py done <id>
```

## รูปแบบไฟล์งาน

```markdown
---
id: 1
title: ทำบอร์ด
status: running
agent: Grok
type: agent
prio: normal
progress: 40
created: 2026-09-29
updated: 2026-09-29
---

## Log

- 2026-09-29 12:00 เริ่มงาน
```

id ถาวร ห้ามเปลี่ยน · log เก่าห้ามลบ · ห้ามลบงานคนอื่น
