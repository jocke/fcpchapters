require 'minitest/autorun'
load File.expand_path('../fcpchapters', __dir__)
class DiagnosticReplayTests < Minitest::Test
  def projects
    path = ENV['FCPCHAPTERS_DIAGNOSTICS']
    skip 'Set FCPCHAPTERS_DIAGNOSTICS to the private timing-replay diagnostic fixture' unless path
    JSON.parse(File.read(path)).fetch('projects')
  end
  def replay(p, validate_timing: true)
    FCPChapters.extract_graph(p.fetch('objects').map { |r| r.merge('md' => r.fetch('metadata')) }, p.fetch('relationships'), project_pk: p.fetch('project_pk'), validate_timing: validate_timing)
  end
  def test_real_projects_reconcile_without_bypassing_timing_checks
    assert_equal 4, projects.length
    projects.each do |p|
      result = replay(p)
      assert_empty result[:chapters]
      assert_operator result[:clips].length, :>, 0
      assert_equal [[], []], FCPChapters.render(result)
    end
  end
  def test_no_chapters_skip_unsupported_timing_but_nested_chapters_do_not
    p = projects.first
    p['objects'].find { |r| r['pk'] == 444 }['metadata']['channelData'] = '<invalid/>'
    result = replay(p, validate_timing: false)
    assert_equal true, result[:timing_skipped]
    assert_equal [[], []], FCPChapters.render(result)
    # A chapter on a connected object must prevent the no-chapter shortcut.
    p['objects'] << {'pk' => -1, 'type' => 'FFAnchoredTimeMarker', 'metadata' => {'isChapter' => true}}
    p['relationships'] << {'parent' => 419, 'child' => -1}
    assert_raises(FCPChapters::Error) { replay(p, validate_timing: false) }
  end
  def test_zero_duration_requires_no_primary_or_connected_items
    p = projects.first
    info = p['objects'].find { |r| r['metadata']['timecodeFrameDuration'] && r['metadata']['mediaRange'] }
    info['metadata']['mediaRange'] = '{(0/1),(0/1)}'
    assert_raises(FCPChapters::Error) { replay(p, validate_timing: false) }
    groups = p['relationships'].select { |e| e['parent'] == p['project_pk'] }.map { |e| e['child'] }
    item_groups = p['objects'].select { |r| groups.include?(r['pk']) && %w[containedItems anchoredItems].include?(r['name']) }
    ids = item_groups.map { |r| r['pk'] }
    p['relationships'].reject! { |e| ids.include?(e['parent']) }
    item_groups.each { |r| r['metadata']['$order'] = [] }
    result = replay(p)
    assert_equal true, result[:empty_project]
    assert_empty result[:chapters]
    assert_equal [[], []], FCPChapters.render(result)
  end
  def test_bad_connected_map_still_rejected_on_its_actual_owner
    p = projects.first
    effect = p['objects'].find { |r| r['pk'] == 444 }
    effect['metadata']['channelData'] = '<invalid/>'
    error = assert_raises(FCPChapters::Error) { replay(p) }
    assert_includes error.message, 'Connected Clip'
    assert_includes error.message, 'missing Time Map curve'
  end
  def test_duration_guard_still_active
    p = projects.last
    info = p['objects'].find { |r| r['metadata']['timecodeFrameDuration'] && r['metadata']['mediaRange'] }
    start, duration = FCPChapters.pair(info['metadata']['mediaRange'])
    info['metadata']['mediaRange'] = "{(#{start}),(#{duration + 1})}"
    error = assert_raises(FCPChapters::Error) { replay(p) }
    assert_includes error.message, 'do not match timeline duration'
  end
end
