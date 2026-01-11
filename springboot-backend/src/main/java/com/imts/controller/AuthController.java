package com.imts.controller;

import com.imts.dto.auth.AuthResponse;
import com.imts.dto.auth.LoginRequest;
import com.imts.dto.auth.RegisterRequest;
import com.imts.service.AuthService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.Map;

/**
 * 认证控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {
    
    private final AuthService authService;
    
    /**
     * 用户注册
     * 
     * POST /api/auth/register
     */
    @PostMapping("/register")
    public Mono<ResponseEntity<AuthResponse>> register(
        @RequestBody RegisterRequest request
    ) {
        log.info("注册请求: username={}", request.getUsername());
        
        return authService.register(request)
            .map(ResponseEntity::ok)
            .onErrorResume(error -> {
                log.error("注册失败", error);
                return Mono.just(ResponseEntity.badRequest().body(
                    AuthResponse.builder()
                        .message(error.getMessage())
                        .build()
                ));
            });
    }
    
    /**
     * 用户登录
     * 
     * POST /api/auth/login
     */
    @PostMapping("/login")
    public Mono<ResponseEntity<AuthResponse>> login(
        @RequestBody LoginRequest request
    ) {
        log.info("登录请求: username={}", request.getUsername());
        
        return authService.login(request)
            .map(ResponseEntity::ok)
            .onErrorResume(error -> {
                log.error("登录失败", error);
                return Mono.just(ResponseEntity.badRequest().body(
                    AuthResponse.builder()
                        .message(error.getMessage())
                        .build()
                ));
            });
    }
    
    /**
     * 获取当前用户信息
     * 
     * GET /api/auth/me
     */
    @GetMapping("/me")
    public Mono<ResponseEntity<AuthResponse>> getCurrentUser(
        @RequestParam("userId") Long userId
    ) {
        return authService.getUserInfo(userId)
            .map(ResponseEntity::ok)
            .onErrorResume(error -> 
                Mono.just(ResponseEntity.notFound().build())
            );
    }
    
    /**
     * 用户登出（前端清除本地存储即可）
     * 
     * POST /api/auth/logout
     */
    @PostMapping("/logout")
    public Mono<ResponseEntity<Map<String, String>>> logout() {
        return Mono.just(ResponseEntity.ok(Map.of(
            "message", "登出成功"
        )));
    }
}
