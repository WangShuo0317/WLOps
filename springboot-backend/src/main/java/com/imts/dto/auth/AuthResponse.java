package com.imts.dto.auth;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 认证响应
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AuthResponse {
    private Long userId;
    private String username;
    private String email;
    private String realName;
    private String role;
    private String message;
}
