<?php

use App\Http\Controllers\Api\HealthController;
use App\Http\Controllers\Api\LessonController;
use App\Http\Controllers\Api\ProgressController;
use Illuminate\Support\Facades\Route;

Route::get('/health', HealthController::class);

Route::get('/lessons', [LessonController::class, 'index']);

Route::post('/progress/sync', [ProgressController::class, 'sync']);
