package com.imts.service;

import com.imts.dto.auth.AuthResponse;
import com.imts.dto.auth.LoginRequest;
import com.imts.dto.auth.RegisterRequest;
import com.imts.entity.User;
import com.imts.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import reactor.core.publisher.Mono;

import java.time.LocalDateTime;
import java.util.Base64;

/**
 * 认证服务
 * 
 * 注意：这是一个简化版本，使用 Base64 编码密码
 * 生产环境应该使用 BCrypt 或其他安全的加密算法
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {
    
    private final UserRepository userRepository;
    
    /**
     * 用户注册
     */
    @Transactional
    public Mono<AuthResponse> register(RegisterRequest request) {
        log.info("用户注册: username={}", request.getUsername());
        
        return Mono.fromCallable(() -> {
            // 检查用户名是否已存在
            if (userRepository.existsByUsername(request.getUsername())) {
                throw new RuntimeException("用户名已存在");
            }
            
            // 检查邮箱是否已存在
            if (request.getEmail() != null && userRepository.existsByEmail(request.getEmail())) {
                throw new RuntimeException("邮箱已被使用");
            }
            
            // 简单的密码加密（Base64）
            // 生产环境应该使用 BCrypt
            String encodedPassword = Base64.getEncoder().encodeToString(
                request.getPassword().getBytes()
            );
            
            // 创建用户
            User user = User.builder()
                .username(request.getUsername())
                .password(encodedPassword)
                .email(request.getEmail())
                .realName(request.getRealName())
                .role("USER")
                .createdAt(LocalDateTime.now())
                .build();
            
            user = userRepository.save(user);
            
            log.info("用户注册成功: userId={}, username={}", user.getId(), user.getUsername());
            
            return AuthResponse.builder()
                .userId(user.getId())
                .username(user.getUsername())
                .email(user.getEmail())
                .realName(user.getRealName())
                .role(user.getRole())
                .message("注册成功")
                .build();
        });
    }
    
    /**
     * 用户登录
     */
    public Mono<AuthResponse> login(LoginRequest request) {
        log.info("用户登录: username={}", request.getUsername());
        
        return Mono.fromCallable(() -> {
            // 查找用户
            log.info("正在查找用户: {}", request.getUsername());
            var userOptional = userRepository.findByUsername(request.getUsername());
            
            if (userOptional.isEmpty()) {
                log.error("用户不存在: {}", request.getUsername());
                throw new RuntimeException("用户名或密码错误");
            }
            
            User user = userOptional.get();
            log.info("找到用户: userId={}, username={}", user.getId(), user.getUsername());
            
            // 验证密码
            String encodedPassword = Base64.getEncoder().encodeToString(
                request.getPassword().getBytes()
            );
            
            log.info("输入密码: {}", request.getPassword());
            log.info("编码后密码: {}", encodedPassword);
            log.info("数据库密码: {}", user.getPassword());
            log.info("密码匹配: {}", user.getPassword().equals(encodedPassword));
            
            if (!user.getPassword().equals(encodedPassword)) {
                log.error("密码不匹配: 输入={}, 数据库={}", encodedPassword, user.getPassword());
                throw new RuntimeException("用户名或密码错误");
            }
            
            log.info("用户登录成功: userId={}, username={}", user.getId(), user.getUsername());
            
            return AuthResponse.builder()
                .userId(user.getId())
                .username(user.getUsername())
                .email(user.getEmail())
                .realName(user.getRealName())
                .role(user.getRole())
                .message("登录成功")
                .build();
        });
    }
    
    /**
     * 获取用户信息
     */
    public Mono<AuthResponse> getUserInfo(Long userId) {
        return Mono.fromCallable(() -> {
            User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("用户不存在"));
            
            return AuthResponse.builder()
                .userId(user.getId())
                .username(user.getUsername())
                .email(user.getEmail())
                .realName(user.getRealName())
                .role(user.getRole())
                .build();
        });
    }
}
