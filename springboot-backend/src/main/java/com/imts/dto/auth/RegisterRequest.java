package com.imts.dto.auth;

import lombok.Data;

/**
 * 注册请求
 */
@Data
public class RegisterRequest {
    private String username;
    private String password;
    private String email;
    private String realName;
}
