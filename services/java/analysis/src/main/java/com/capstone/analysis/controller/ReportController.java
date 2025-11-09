package com.capstone.analysis.controller;

import com.capstone.analysis.dto.ReportDtos.*;
import com.capstone.analysis.service.ReportService;
import org.springframework.core.io.Resource;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.Map;

import static org.springframework.http.HttpStatus.INTERNAL_SERVER_ERROR;
import static org.springframework.http.HttpStatus.NOT_FOUND;

/**
 * 리포트 생성 API 컨트롤러
 * 
 * 분석 결과를 기반으로 자동 리포트를 생성하는 REST API를 제공합니다.
 * 감성, 트렌드, 요약 리포트 생성 및 관리 기능을 제공합니다.
 */
@RestController
@RequestMapping("/api/v1/reports")
public class ReportController {
    
    private final ReportService reportService;
    
    /**
     * 생성자 주입을 통한 의존성 주입
     * 
     * @param reportService 리포트 서비스
     */
    public ReportController(ReportService reportService) {
        this.reportService = reportService;
    }
    
    /**
     * 리포트 생성
     * 
     * 지정된 타입과 파라미터에 따라 분석 리포트를 자동 생성합니다.
     * 대용량 리포트는 백그라운드에서 비동기로 처리됩니다.
     * 
     * @param request 리포트 생성 요청 데이터 (타입, 제목, 파라미터)
     * @return ReportResponse 생성된 리포트 정보
     */
    @PostMapping("/generate")
    public ResponseEntity<ReportResponse> generateReport(
            @RequestBody ReportRequest request) {
        try {
            ReportResponse response = reportService.generateReport(request);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to generate report: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 리포트 목록 조회
     * 
     * 생성된 리포트 목록을 페이지네이션과 함께 조회합니다.
     * 타입별 필터링을 지원합니다.
     * 
     * @param reportType 리포트 타입 필터 (sentiment/trend/summary)
     * @param limit 조회할 최대 개수 (기본: 10)
     * @param offset 시작 위치 (기본: 0)
     * @return List<ReportResponse> 리포트 목록
     */
    @GetMapping
    public ResponseEntity<List<ReportResponse>> listReports(
            @RequestParam(required = false) String reportType,
            @RequestParam(defaultValue = "10") int limit,
            @RequestParam(defaultValue = "0") int offset) {
        try {
            List<ReportResponse> reports = reportService.listReports(
                    reportType, 
                    limit, 
                    offset
            );
            return ResponseEntity.ok(reports);
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to retrieve report list: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 특정 리포트 조회
     * 
     * ID를 통해 특정 리포트의 상세 내용을 조회합니다.
     * 
     * @param reportId 리포트 ID
     * @return ReportResponse 리포트 상세 정보
     */
    @GetMapping("/{reportId}")
    public ResponseEntity<ReportResponse> getReport(
            @PathVariable Long reportId) {
        try {
            ReportResponse report = reportService.getReport(reportId);
            
            if (report == null) {
                throw new ResponseStatusException(
                        NOT_FOUND, 
                        "Report not found with ID: " + reportId
                );
            }
            
            return ResponseEntity.ok(report);
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to retrieve report: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 리포트 삭제
     * 
     * 지정된 리포트를 삭제합니다.
     * 실제 삭제 대신 비활성화하여 데이터를 보존할 수 있습니다.
     * 
     * @param reportId 삭제할 리포트 ID
     * @return Map<String, String> 삭제 성공 메시지
     */
    @DeleteMapping("/{reportId}")
    public ResponseEntity<Map<String, String>> deleteReport(
            @PathVariable Long reportId) {
        try {
            boolean success = reportService.deleteReport(reportId);
            
            if (!success) {
                throw new ResponseStatusException(
                        NOT_FOUND, 
                        "Report not found with ID: " + reportId
                );
            }
            
            return ResponseEntity.ok(Map.of("message", "Report deleted successfully"));
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to delete report: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 리포트 다운로드
     * 
     * 리포트를 지정된 형식으로 다운로드합니다.
     * JSON, PDF, Excel 형식을 지원합니다.
     * 
     * @param reportId 다운로드할 리포트 ID
     * @param format 파일 형식 (json/pdf/excel, 기본: json)
     * @return Resource 다운로드 파일 리소스
     */
    @GetMapping("/{reportId}/download")
    public ResponseEntity<Resource> downloadReport(
            @PathVariable Long reportId,
            @RequestParam(defaultValue = "json") String format) {
        try {
            Resource resource = reportService.downloadReport(reportId, format);
            
            if (resource == null) {
                throw new ResponseStatusException(
                        NOT_FOUND, 
                        "Report not found with ID: " + reportId
                );
            }
            
            String contentType = switch (format.toLowerCase()) {
                case "pdf" -> "application/pdf";
                case "excel", "xlsx" -> "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
                default -> "application/json";
            };
            
            return ResponseEntity.ok()
                    .header("Content-Type", contentType)
                    .header("Content-Disposition", 
                            "attachment; filename=\"report_" + reportId + "." + format + "\"")
                    .body(resource);
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to download report: " + e.getMessage(), 
                    e
            );
        }
    }
}
