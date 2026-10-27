<?php

namespace Tests\Feature;

use Tests\TestCase;

class ApiContractTest extends TestCase
{
    public function test_health_endpoint_returns_ok(): void
    {
        $response = $this->getJson('/api/health');

        $response->assertOk()
            ->assertJsonPath('status', 'ok')
            ->assertJsonPath('service', 'the-seed-api');
    }

    public function test_lessons_endpoint_lists_seed_lesson(): void
    {
        $response = $this->getJson('/api/lessons');

        $response->assertOk()
            ->assertJsonPath('data.0.id', 'demo_sol_overview');
    }

    public function test_progress_sync_accepts_valid_payload(): void
    {
        $response = $this->postJson('/api/progress/sync', [
            'player_name' => 'Cadete',
            'completed_lessons' => ['demo_sol_overview'],
            'solved_puzzles' => [],
            'stars_earned' => 1,
        ]);

        $response->assertOk()
            ->assertJsonPath('status', 'synced')
            ->assertJsonPath('received.stars_earned', 1);
    }

    public function test_progress_sync_rejects_invalid_stars(): void
    {
        $response = $this->postJson('/api/progress/sync', [
            'stars_earned' => -3,
        ]);

        $response->assertStatus(422);
    }
}
