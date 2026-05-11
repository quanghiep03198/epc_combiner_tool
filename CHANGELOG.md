# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2024-10-02

### Features

- Login with MES account
- Searching command number and order information
- Integrate scanning EPC with UHF RFID reader
- Store EPC combination information to SQL Server

## [1.1] - 2025-04-26

### Fixed
- Translate combine EPC failure message
- Escape single quotes in JSON data for database insertion

## [1.1.1-rc] - 2025-10-04

### Features 
- Refetch command number information
- Continuous Integration: Windows installation downloader

### Changed
- Apply debounce decorator
- Update settings form layout 
- Refactor data service layer with new database service

### Fixed 
- Parallel SQL executions
- Debouncing combination submission
- EPC Combination form validation
- Multi-language display

## [1.1.2] - 2025-10-08

### Added

- CI/CD on new version release created

### Features

- Check for new version if available
- Install new version console window

### Fixed

- Clean up scanned EPC after writing CSV successfully

## [1.3.0] - 2026-02-18

### Features

- Theme manager
- Set window icon for the main application window
- Prevent context menu for side toolbar, status bar, and app toolbar
- Remove unused zoom-in and zoom-out SVG icons
- Add department translations and improve station selection logic
- Add confirmation messages for suborder migration and improve UI elements 
- Migrate CO & pre-order to official sub-order

## [1.3.1] - 2026-02-23

### Features

- Enhance AdditionalQtyDelegate with theme-aware styling for QLineEdit
- Update overlay background color to use theme colors
- Add Windows installer for version 1.3.1

## [1.3.2] - 2026-02-25

### Features

- Remove SVG icon helper module
- Ensure required sections exist in config file with sensible defaults
- Enhance file replacement strategies with robocopy and pending rename options
- Update theme management and remove deprecated stylesheets

## [1.3.3] - 2026-05-04

### Added

- Update version to 1.3.2 and add new Windows installer

### Fixed

- Correct column name of order detail table in multi-languages

## [1.3.4] - 2026-05-11

### Fixed

- Update translations for customer order fields and improve order detail table headers

[1.1]: https://github.com/quanghiep03198/epc_combiner_tool/releases/tag/v1.1
[1.1.1-rc]: https://github.com/quanghiep03198/epc_combiner_tool/releases/tag/v1.1.1-rc
[1.1.2]: https://github.com/quanghiep03198/epc_combiner_tool/releases/tag/v1.1.2
[1.3.0]: https://github.com/quanghiep03198/epc_combiner_tool/releases/tag/v1.3.0
[1.3.1]: https://github.com/quanghiep03198/epc_combiner_tool/releases/tag/v1.3.1
[1.3.2]: https://github.com/quanghiep03198/epc_combiner_tool/releases/tag/v1.3.2
[1.3.3]: https://github.com/quanghiep03198/epc_combiner_tool/releases/tag/v1.3.3
[1.3.4]: https://github.com/quanghiep03198/epc_combiner_tool/releases/tag/v1.3.4