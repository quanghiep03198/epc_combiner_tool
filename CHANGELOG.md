# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2024-10-02

### Added

- Login with MES account
- Searching command number and order information
- Integrate scanning EPC with UHF RFID reader
- Store EPC combination information to SQL Server

## [1.1] - 2025-04-26

### Fixed
- Translate combine EPC failure message
- Escape single quotes in JSON data for database insertion

## [1.1.1] - 2025-10-04

### Added 
- Refetch command number information
- Continuos Integration: Windows installation downloader

### Changed
- Apply debounce decorator
- Update settings form layout 
- Refactor data service layer with new database service

### Fixed 
- Parallel SQL executions
- Debouncing combination submission
- EPC Combination form validation
- Multi-language display

[1.1]: https://github.com/quanghiep03198/epc_combiner_tool/releases/tag/v1.1
[1.1.1]: https://github.com/username/epc-combiner-tool/releases/tag/v1.1.1