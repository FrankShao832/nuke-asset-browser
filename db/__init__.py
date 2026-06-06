"""数据存储层 — PostgreSQL 主力 + JSON 离线兜底。

提供 DraftStorage 抽象基类及 PG/JSON 两种实现，
支持自动选择存储后端和断线恢复同步。
"""
