# Requirements Document

## Introduction

This feature involves migrating the We All Code Django application from the deprecated Poetry buildpack to Heroku's native Python buildpack with uv support. The current Poetry buildpack is no longer maintained and Heroku now provides native Poetry support with better performance and caching. This migration will ensure continued deployment reliability and take advantage of improved build times.

## Requirements

### Requirement 1

**User Story:** As a developer, I want to use Heroku's native Python buildpack instead of the deprecated Poetry buildpack, so that I can ensure reliable deployments with better performance and caching.

#### Acceptance Criteria

1. WHEN the application is deployed to Heroku THEN the system SHALL use Heroku's native Python buildpack instead of the deprecated Poetry buildpack
2. WHEN dependencies are installed during deployment THEN the system SHALL use Poetry directly rather than exporting to requirements.txt
3. WHEN subsequent deployments occur THEN the system SHALL benefit from Poetry install caching for faster rebuilds
4. WHEN the buildpack configuration is checked THEN the system SHALL show no deprecated Poetry buildpack references

### Requirement 2

**User Story:** As a developer, I want the Python version to be explicitly specified for Heroku, so that deployments use the correct Python version consistently.

#### Acceptance Criteria

1. WHEN Heroku builds the application THEN the system SHALL use Python 3.11.9 as specified in the project configuration
2. WHEN the Python version is checked THEN the system SHALL match the version specified in poetry.lock metadata
3. IF the Python version is not explicitly specified THEN the deployment SHALL fail with a clear error message

### Requirement 3

**User Story:** As a developer, I want to remove all deprecated buildpack configurations, so that the deployment process is clean and uses only supported tools.

#### Acceptance Criteria

1. WHEN buildpack configurations are reviewed THEN the system SHALL contain no references to the deprecated Poetry buildpack
2. WHEN the application is deployed THEN the system SHALL not attempt to use any deprecated buildpacks
3. WHEN buildpack removal is complete THEN the system SHALL maintain all existing functionality without regression

### Requirement 4

**User Story:** As a developer, I want to verify the migration works correctly, so that I can be confident the new buildpack configuration deploys successfully.

#### Acceptance Criteria

1. WHEN the migration is complete THEN the application SHALL deploy successfully to Heroku
2. WHEN the deployed application is tested THEN all existing functionality SHALL work as expected
3. WHEN deployment logs are reviewed THEN they SHALL show Poetry being used directly without requirements.txt export
4. WHEN build times are compared THEN subsequent deployments SHALL be faster due to Poetry caching
