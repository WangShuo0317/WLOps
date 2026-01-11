package com.imts.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 用户实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "users")
public class User {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    /**
     * 用户名（唯一）
     */
    @Column(unique = true, nullable = false, length = 50)
    private String username;
    
    /**
     * 密码（加密存储）
     */
    @Column(nullable = false)
    private String password;
    
    /**
     * 邮箱
     */
    @Column(length = 100)
    private String email;
    
    /**
     * 真实姓名
     */
    @Column(length = 50)
    private String realName;
    
    /**
     * 角色（USER, ADMIN）
     */
    @Builder.Default
    @Column(length = 20)
    private String role = "USER";
    
    /**
     * 创建时间
     */
    @Column(nullable = false)
    private LocalDateTime createdAt;
    
    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
