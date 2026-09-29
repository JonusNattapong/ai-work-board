# AGENTS.md

โปรเจกต์นี้คือบอร์ดงาน local-first สำหรับมนุษย์และเอเจนต์ AI

## โครงสร้าง

- `work-items/` — แหล่งจริง หนึ่งงาน = หนึ่งไฟล์ `.md`
  - โฟลเดอร์ย่อยคือสถานะ: `queued/` `running/` `review/` `done/`
- `app/index.html` — หน้าบอร์ดสำหรับคนดู
- `cli/task.py` — CLI ที่เอเจนต์ใช้อัปเดตสถานะ

## คำสั่ง

```bash
python3 cli/task.py ls
python3 cli/task.py add "ชื่องาน" --agent Grok --type agent --prio normal
python3 cli/task.py start <id>
python3 cli/task.py log <id> "สรุปสั้น"
python3 cli/task.py progress <id> 40
python3 cli/task.py review <id>
python3 cli/task.py done <id>
python3 cli/task.py serve
```

## กติกา

1. ก่อนลงมือต้องมีใบงาน ถ้าไม่มีให้สร้างด้วย `add`
2. เริ่มงานต้อง `start`
3. ทุกความคืบหน้าต้อง `log` และตั้ง `progress` เป็นขั้น 10
4. ใกล้จบส่ง `review` ใช้ได้จริงค่อย `done`
5. ห้ามเปลี่ยน id ห้ามลบ log เก่า ห้ามลบงานคนอื่น
6. อย่าเก็บสถานะไว้แค่ในแชท — ต้องเขียนลงไฟล์เสมอ
