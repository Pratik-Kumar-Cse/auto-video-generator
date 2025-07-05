// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

// Switch to the video_generator database
db = db.getSiblingDB('video_generator');

// Create collections with validation schemas
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['email', 'password', 'created_at'],
      properties: {
        email: {
          bsonType: 'string',
          description: 'User email address'
        },
        password: {
          bsonType: 'string',
          description: 'Hashed password'
        },
        first_name: {
          bsonType: 'string',
          description: 'User first name'
        },
        last_name: {
          bsonType: 'string',
          description: 'User last name'
        },
        role: {
          bsonType: 'string',
          enum: ['user', 'admin', 'moderator'],
          description: 'User role'
        },
        is_active: {
          bsonType: 'bool',
          description: 'User active status'
        },
        created_at: {
          bsonType: 'date',
          description: 'User creation timestamp'
        },
        updated_at: {
          bsonType: 'date',
          description: 'User last update timestamp'
        }
      }
    }
  }
});

db.createCollection('videos', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'script_id', 'status', 'created_at'],
      properties: {
        user_id: {
          bsonType: 'string',
          description: 'ID of the user who owns the video'
        },
        script_id: {
          bsonType: 'string',
          description: 'ID of the script used for the video'
        },
        voice_id: {
          bsonType: 'string',
          description: 'ID of the voice used'
        },
        avatar_id: {
          bsonType: 'string',
          description: 'ID of the avatar used'
        },
        template_id: {
          bsonType: 'string',
          description: 'ID of the template used'
        },
        status: {
          bsonType: 'string',
          enum: ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'TIMED_OUT'],
          description: 'Video processing status'
        },
        view_type: {
          bsonType: 'string',
          enum: ['LANDSCAPE', 'PORTRAIT', 'SQUARE'],
          description: 'Video view type'
        },
        created_at: {
          bsonType: 'date',
          description: 'Video creation timestamp'
        },
        updated_at: {
          bsonType: 'date',
          description: 'Video last update timestamp'
        }
      }
    }
  }
});

db.createCollection('subscriptions', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'plan_type', 'status', 'start_date', 'end_date'],
      properties: {
        user_id: {
          bsonType: 'string',
          description: 'ID of the user'
        },
        plan_type: {
          bsonType: 'string',
          enum: ['free', 'basic', 'pro', 'enterprise'],
          description: 'Subscription plan type'
        },
        status: {
          bsonType: 'string',
          enum: ['active', 'cancelled', 'expired'],
          description: 'Subscription status'
        },
        start_date: {
          bsonType: 'date',
          description: 'Subscription start date'
        },
        end_date: {
          bsonType: 'date',
          description: 'Subscription end date'
        }
      }
    }
  }
});

db.createCollection('usage', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'action', 'created_at'],
      properties: {
        user_id: {
          bsonType: 'string',
          description: 'ID of the user'
        },
        action: {
          bsonType: 'string',
          description: 'Action performed'
        },
        metadata: {
          bsonType: 'object',
          description: 'Additional metadata'
        },
        created_at: {
          bsonType: 'date',
          description: 'Usage timestamp'
        }
      }
    }
  }
});

db.createCollection('tokens', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['token', 'user_id', 'revoked_at'],
      properties: {
        token: {
          bsonType: 'string',
          description: 'JWT token'
        },
        user_id: {
          bsonType: 'string',
          description: 'ID of the user'
        },
        revoked_at: {
          bsonType: 'date',
          description: 'Token revocation timestamp'
        },
        expires_at: {
          bsonType: 'date',
          description: 'Token expiration timestamp'
        }
      }
    }
  }
});

db.createCollection('scripts', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['user_id', 'type', 'status', 'created_at'],
      properties: {
        user_id: {
          bsonType: 'string',
          description: 'ID of the user who owns the script'
        },
        type: {
          bsonType: 'string',
          enum: ['TOPIC', 'VIDEO', 'BLOG', 'CUSTOM'],
          description: 'Script generation type'
        },
        status: {
          bsonType: 'string',
          enum: ['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'],
          description: 'Script processing status'
        },
        language: {
          bsonType: 'string',
          enum: ['EN', 'ES', 'FR', 'DE', 'IT', 'PT', 'RU', 'JA', 'KO', 'ZH'],
          description: 'Script language'
        },
        tone: {
          bsonType: 'string',
          enum: ['PROFESSIONAL', 'CASUAL', 'FRIENDLY', 'FORMAL', 'HUMOROUS', 'EDUCATIONAL'],
          description: 'Script tone'
        },
        audience: {
          bsonType: 'string',
          enum: ['GENERAL', 'CHILDREN', 'TEENS', 'ADULTS', 'SENIORS', 'PROFESSIONALS'],
          description: 'Target audience'
        },
        content: {
          bsonType: 'object',
          description: 'Generated script content'
        },
        generation_params: {
          bsonType: 'object',
          description: 'Parameters used for generation'
        },
        is_public: {
          bsonType: 'bool',
          description: 'Whether script is publicly visible'
        },
        task_id: {
          bsonType: 'string',
          description: 'Celery task ID for generation'
        },
        created_at: {
          bsonType: 'date',
          description: 'Script creation timestamp'
        },
        updated_at: {
          bsonType: 'date',
          description: 'Script last update timestamp'
        },
        completed_at: {
          bsonType: 'date',
          description: 'Script completion timestamp'
        }
      }
    }
  }
});

// Create indexes for better performance
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ created_at: -1 });

db.videos.createIndex({ user_id: 1 });
db.videos.createIndex({ status: 1 });
db.videos.createIndex({ created_at: -1 });
db.videos.createIndex({ user_id: 1, status: 1 });
db.videos.createIndex({ user_id: 1, created_at: -1 });

db.subscriptions.createIndex({ user_id: 1 });
db.subscriptions.createIndex({ status: 1 });
db.subscriptions.createIndex({ end_date: 1 });
db.subscriptions.createIndex({ user_id: 1, status: 1 });

db.usage.createIndex({ user_id: 1 });
db.usage.createIndex({ action: 1 });
db.usage.createIndex({ created_at: -1 });
db.usage.createIndex({ user_id: 1, action: 1 });
db.usage.createIndex({ user_id: 1, created_at: -1 });

db.tokens.createIndex({ token: 1 }, { unique: true });
db.tokens.createIndex({ user_id: 1 });
db.tokens.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });

db.scripts.createIndex({ user_id: 1 });
db.scripts.createIndex({ type: 1 });
db.scripts.createIndex({ status: 1 });
db.scripts.createIndex({ language: 1 });
db.scripts.createIndex({ is_public: 1 });
db.scripts.createIndex({ created_at: -1 });
db.scripts.createIndex({ user_id: 1, status: 1 });
db.scripts.createIndex({ user_id: 1, created_at: -1 });
db.scripts.createIndex({ type: 1, language: 1 });
db.scripts.createIndex({ is_public: 1, created_at: -1 });
db.scripts.createIndex({ "content.title": "text", "content.description": "text" });

// Create a default admin user (optional)
db.users.insertOne({
  email: 'admin@videogen.com',
  password: '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5S/kS', // password: admin123
  first_name: 'Admin',
  last_name: 'User',
  role: 'admin',
  is_active: true,
  permissions: ['all'],
  created_at: new Date(),
  updated_at: new Date()
});

print('MongoDB initialization completed successfully!');
print('Collections created: users, videos, scripts, subscriptions, usage, tokens');
print('Indexes created for optimal performance');
print('Default admin user created: admin@videogen.com / admin123');