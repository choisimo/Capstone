package com.capstone.analysis.dto;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

public class ReportDtos {
    
    public record ReportRequest(
            String report_type,
            String title,
            Map<String, Object> parameters,
            OffsetDateTime start_date,
            OffsetDateTime end_date
    ) {}
    
    public record ReportResponse(
            Long report_id,
            String title,
            String report_type,
            Map<String, Object> content,
            OffsetDateTime created_at,
            String download_url
    ) {}
    
    public record ReportListResponse(
            List<ReportResponse> reports,
            int total,
            int offset,
            int limit
    ) {}
}
